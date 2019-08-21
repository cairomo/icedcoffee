import csv
import copy
import pdb

output = []
with open('images.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            output.append(row)
            line_count += 1
        else:
            labels = row[7].strip('[]')
            labels = labels.split(',')
            counter = 1
            for l in labels: # if no labels, skips
                single_row = copy.deepcopy(row)
                single_row[7] = l.strip('"')
                single_row[0] = row[0].strip(" ") + "_" + str(counter)
                #pdb.set_trace()
                output.append(single_row)
                counter = counter + 1
            line_count += 1
    print(f'Processed {line_count} lines.')

with open('images_expanded.csv', mode='w') as img_file:
    employee_writer = csv.writer(img_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for row in output:
        employee_writer.writerow(row)