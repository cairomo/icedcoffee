"""
dash sample app
cairo mo 2019
iced coffee svg from https://www.svgrepo.com/svg/78379/iced-coffee
"""
import copy
import pathlib
import dash
import math
import pandas as pd
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import dash_dangerously_set_inner_html
from werkzeug.wsgi import DispatcherMiddleware
import plotly.graph_objects as go
import json
import io
import pdb
from flask import Flask 
from flask_cors import CORS

import gspread
from oauth2client.service_account import ServiceAccountCredentials

df = None
keyFile = open('mapboxkey.txt','r')
mapbox_access_token = keyFile.readline().rstrip()
def load_data():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    SHEET_ID = "1XMwuPZvnCi7nE7LlSBtDDbN6F42N1lR2kKO30AmhSx0"
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("iced coffee data").sheet1

    list_of_hashes = sheet.get_all_records()
    df = pd.DataFrame(list_of_hashes)
    return df

# Multi-dropdown options
from controls import SEVERITIES
# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()


ROAST_TYPES = dict(
    LR='Light Roast',
    MR='Medium Roast',
    DR='Dark Roast',
)

# flask_app = Flask(__name__)
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]#, server=flask_app, url_base_pathname='/dash/'
)
flask_app = app.server
# application = DispatcherMiddleware(flask_app, {'/dash': app.server})

# # server = Flask(__name__)

# CORS(flask_app)

# @flask_app.route('/plotly_dashboard') 
# def render_dashboard():
#     return flask.redirect('/dash')

# Create controls
severity_options = [
    # {"label": str(SEVERITIES[well_status]), "value": str(well_status)}
    {"label": str(SEVERITIES[well_status]), "value": str(SEVERITIES[well_status])}
    for well_status in SEVERITIES
]

roast_type_options = [
    # {"label": str(ROAST_TYPES[well_type]), "value": str(well_type)}
    {"label": str(ROAST_TYPES[well_type]), "value": str(ROAST_TYPES[well_type])}
    for well_type in ROAST_TYPES
]

company_id = '345'
project_id = "'test_project_id'"

df = load_data()

# Create global chart template

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Iced Coffee Locations",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=-122.167, lat=37.429),
        zoom=14,
    ),
)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        # empty div to store csv
        html.Div(
            [
                html.Div(
                    [
                        
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Img(
                                    src=app.get_asset_url("icedcoffee.svg"),
                                    id="plotly-image",
                                    style={
                                        "height": "80px",
                                        "width": "auto",
                                        "margin-bottom": "5px",
                                    },
                                )
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div( # row
            [
                html.Div(
                    [
                        html.P("Filter by price per ounce:", className="control_label"),
                        dcc.RangeSlider(
                            id='well_statuses',
                            min=0,
                            max=0.5,
                            step=0.05,
                            value=[0, 0.3],
                            marks={
                                0: '0¢',
                                0.1: '10¢',
                                0.15: '15¢',
                                0.2: '20¢',
                                0.25: '25¢',
                                0.3:'30¢',
                                0.35:'35¢',
                                0.4:'40¢',
                                0.45:'45¢',
                                0.5:'50¢'
                            },
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container six columns",
                    id="price-filter-options",
                ),
                html.Div(
                    [
                        html.P("Filter by fault type:", className="control_label"),
                        dcc.RadioItems(
                            id="well_type_selector",
                            options=[
                                {"label": "All ", "value": "all"},
                                # {"label": "Productive only ", "value": "productive"},
                                {"label": "Customize ", "value": "custom"},
                            ],
                            value="all",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        dcc.Dropdown(
                            id="well_types",
                            options=roast_type_options,
                            multi=True,
                            # value=list(ROAST_TYPES.keys()),
                            value=[*ROAST_TYPES.values()],
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container six columns",
                    id="roast-filter-options",
                )
            ],
            className="row flex-display",
            id="cross-filter-options",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="main_graph")],
                    className="pretty_container nine columns",
                ),
                html.Div(
                    children='',
                    id="individual_graph",
                    #[dcc.Markdown(id="individual_graph")],
                    className="pretty_container three columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Helper functions

def filter_dataframe(df, well_statuses, well_types):
    if df is not None:
        dff = df[
            (df["price per oz"] > well_statuses[0]) &
            (df["price per oz"] < well_statuses[1]) &
            df["roast"].isin(well_types)
        ]
    else:
        dff = None
    return dff


# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("main_graph", "figure")],
)


@app.callback(
    Output("aggregate_data", "data"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
    ],
)
def update_production_text(well_statuses, well_types):
    dff = filter_dataframe(df, well_statuses, well_types)
    selected = dff["name"].values
    return selected


# Radio -> multi
@app.callback(Output("well_types", "value"), [Input("well_type_selector", "value")])
def display_type(selector):
    if selector == "all":
        return list(ROAST_TYPES.values())
    return []


# Selectors -> main graph
@app.callback(
    Output("main_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
    ],
    # [State("lock_selector", "value"), State("main_graph", "relayoutData")],
    [State("main_graph", "relayoutData")],
)
def make_main_figure(
    # well_statuses, well_types, selector, main_graph_layout
    well_statuses, well_types, main_graph_layout
):
    dff = filter_dataframe(df, well_statuses, well_types)
    traces = []

    for well_type, dfff in dff.groupby("roast"):
        df_custom_ = dfff.copy(deep=True)
        #pdb.set_trace()
        lats = dfff['lat'].tolist()
        lons = dfff['long'].tolist()
        df_custom = df_custom_.T # transpose
        length = df_custom.shape[1]
        rows = []
        cols = list(df_custom.columns.values)
        for i in cols:
            rows.append(df_custom[i].to_list())
        # pdb.set_trace()
        trace = dict(
            type="scattermapbox",
            lon=lons,
            lat=lats,
            # text=well_type,
            customdata=rows,
            name=well_type,
            marker=dict(size=9, opacity=0.9, color='rgb(243,181,200)'),
            showlegend=False
        )
        traces.append(trace)
    if main_graph_layout is not None: # and "locked" in selector:
        lon = float(main_graph_layout.get("mapbox", {}).get("center", {}).get("lon", "-122.16726"))
        lat = float(main_graph_layout.get("mapbox", {}).get("center", {}).get("lat", "37.429422"))
        zoom = float(main_graph_layout.get("mapbox", {}).get("zoom", 14))
        layout["mapbox"]["center"]["lon"] = lon
        layout["mapbox"]["center"]["lat"] = lat
        layout["mapbox"]["zoom"] = zoom

    figure = dict(data=traces, layout=layout)
    return figure


# Main graph -> individual graph
@app.callback(Output("individual_graph", "children"), [Input("main_graph", "hoverData")])
def make_individual_figure(main_graph_hover):
    temp = ['NONE', 0, '20oz', 0.05, 'Notes', 'Roast', 'Address']
    if main_graph_hover is None:
        main_graph_hover = {
            "points": [
                {"curveNumber": 4, "pointNumber": 569, "customdata": temp}
            ]
        }
    imgurl = ""
    if main_graph_hover is None:
        imgurl = app.get_asset_url("placeholder.png")
    else:
        chosen = [point["customdata"] for point in main_graph_hover["points"]]
        data = chosen[0]
        baseUrl = "https://maps.google.com/?q="
        #pdb.set_trace()
        if data[0] == 'NONE':
            html = ("<div id='infotext'><h4>Hover over a map point to see more</h4></div>")
        else:
            lat = data[2]
            lon = data[3]
            url = baseUrl + str(lat) + "," + str(lon)
            html = ("<div id='infotext'><h4>"+ data[4] +"</h4> <br>" + 
                    "<b>Price:</b>" + str(data[6]) + " for " + data[9] +
                     " ("+ str(data[7])+" per oz)" +
                    "<br><b>Flavour profile:</b> " + data[5] + " -- " + data[8] + 
                    "<br><b>Address:</b> <em><a href='" + url + "'>" + data[0] + "</a></em></div>")
    
    return dash_dangerously_set_inner_html.DangerouslySetInnerHTML(html)

def resample(g, time):
    temp_g = g.resample(time)
    y_val = temp_g["name"].count()
    dates = temp_g.count().index
    x_val = [None] * len(dates)
    counter = 0
    for d in dates:
        x_val[counter] = d.strftime('%b %d, %Y')
        counter += 1
    retval = [{"y":y_val.to_list()}, {"x":x_val}]
    return retval

app.component_suites = [
    'dash_core_components',
    'dash_html_components'
]
# Main
if __name__ == "__main__":
    #app.run_server(debug=False, port=8080) # for deploying to gae
    app.run_server(debug=True)