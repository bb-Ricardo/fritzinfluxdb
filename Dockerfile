FROM python:3.9-slim

# Make the /app dir
RUN mkdir /app

# Set the working directory to /app
WORKDIR /app

# Copy required files to /app
COPY fritzinfluxdb.py requirements.txt /app/
COPY fritzinfluxdb /app/fritzinfluxdb

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# run daemon
CMD [ "python", "/app/fritzinfluxdb.py" ]

# EOF
