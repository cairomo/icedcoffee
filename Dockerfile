# Use an official Python runtime as a parent image
FROM python:3.6-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV NAME World
ENV PORT 8080

# Run app.py when the container launches
# CMD ["python", "app.py"]
# CMD ["gunicorn", "-b","4000:80", "app:flask_app", "-t", "3600"]

# Deploy to GAE
CMD exec gunicorn -b :8080 app:flask_app --timeout 1800