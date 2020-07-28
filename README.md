# Fritz InfluxDb

Fritz InfluxDb is a tiny daemon written in python to fetch data from a fritz box router and writes it to influxdb.
It is equal capable as fritzcollectd and directly writing to influxdb.

# Setup
```
cd /opt
git clone <this_repo_url>
virtualenv --no-site-packages venv
. ./venv/bin/activate
pip -r requirements.txt
cp /opt/fritzinfluxdb/fritzinfluxdb.service /etc/systemd/system
systemctl daemon-reload
systemctl start fritzinfluxdb
systemctl enable fritzinfluxdb
```

## Run with Docker
```
git clone <this_repo_url>
cd fritzinfluxdb
docker build -t fritzinfluxdb .
```

Copy the config from the [example](default.ini) to ```my-frtizinfluxdb.ini``` and edit
the settings.

Now you should be able to run the image with following command
```
docker run -d -v /PATH/TO/my-frtizinfluxdb.ini:/app/idefault.ini --name fritzinfluxdb fritzinfluxdb
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
