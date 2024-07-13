FROM python:3.12-slim

# Make the /app dir
RUN mkdir /app

# Set the working directory to /app
WORKDIR /app

# Copy required files to /app
COPY fritzinfluxdb.py requirements.txt /app/
COPY fritzinfluxdb /app/fritzinfluxdb

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && \
    PYTHONDONTWRITEBYTECODE=1 pip install --no-compile --no-cache-dir -r requirements.txt && \
    apt-get remove --yes gcc g++ && \
    apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/apt/lists/*

# run daemon
CMD [ "python", "/app/fritzinfluxdb.py", "-d" ]

# EOF
