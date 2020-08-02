# Fritz InfluxDb

Fritz InfluxDb is a tiny daemon written in python to fetch data from a fritz box router and writes it to influxdb.
It is equal capable as fritzcollectd and directly writing to influxdb.

# Setup
* here we assume we install in ```/opt```

## Ubuntu 18.04
```
sudo apt-get install virtualenv
cd /opt
git clone https://github.com/yunity/fritzinfluxdb.git
cd fritzinfluxdb
git checkout python2.7
virtualenv -p python2 .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## RHEL/CentOS 7 with EPEL
```
yum install git python-virtualenv
cd /opt
git clone https://github.com/yunity/fritzinfluxdb.git
cd fritzinfluxdb
git checkout python2.7
virtualenv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

* modify your configuration and test it
```
./fritzinfluxdb.py
```

## Install as systemd service
Ubuntu
```
cp /opt/fritzinfluxdb/fritzinfluxdb.service /etc/systemd/system
```
RHEL/CentOS
```
sed -e 's/nogroup/nobody/g' /opt/fritzinfluxdb/fritzinfluxdb.service > /etc/systemd/system/fritzinfluxdb.service
```

```
systemctl daemon-reload
systemctl start fritzinfluxdb
systemctl enable fritzinfluxdb
```

# Grafana

Use ```grafana_dashboard_fritzbox.json``` to import this dashboard.
This was heavily inspired from: https://grafana.com/dashboards/713

![Grafan Dashboard](grafana_dashboard.jpg)

# Configure more attributes

check here to find a overview of more attributes which probaly could be added
https://wiki.fhem.de/w/index.php?title=FRITZBOX

# License
>You can check out the full license [here](LICENSE.txt)

This project is licensed under the terms of the **MIT** license.
