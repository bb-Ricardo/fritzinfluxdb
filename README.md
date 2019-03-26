# Fritz InfluxDb

Fritz InfluxDb is a tiny daemon written in python to fetch data from a fritz box router and writes it to influxdb.
It is equal capable as fritzcollectd and directly writing to influxdb.

# Setup
```
cd /opt
git clone [.]
virtualenv --no-site-packages venv
. ./venv/bin/activate
pip -r requirements.txt
cp /opt/fritzinfluxdb/fritzinfluxdb.service /etc/systemd/system
systemctl daemon-reload
systemctl start fritzinfluxdb
systemctl enable fritzinfluxdb
```
