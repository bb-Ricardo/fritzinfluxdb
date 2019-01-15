# Fritz InfluxDb

Fritz InfluxDb is a tiny daemon written in python to fetch data from a fritz box router and writes it to influxdb.
It is similar but less capable than fritzcollectd but directly writing the influxdb http protocol.

# Setup
```
virtualenv --no-site-packages venv
. ./venv/bin/activate
pip -r requirements.txt
```
