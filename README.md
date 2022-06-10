# Fritz InfluxDB

"fritzinfluxdb" is a tool written in python to fetch data from a FritzBox router and writes it to InfluxDB.
It is equal capable as fritzcollectd and directly writing to InfluxDB.

Both InfluxDB 1 and InfluxDB 2 are supported

![Grafana Dashboard](grafana/grafana_dashboard.png)


## IMPORTANT:
In order work properly you need to enable "permit access for applications" and "state data via UPnP"


## Requirements
* python3.6 or newer
* influxdb (InfluxDB 1)
* influxdb_client (InfluxDB 2)
* fritzconnection
* pytz

It was tested using FritzOS 7.29. It should work on older versions but some values might be missing.

DSL and Cable Modem FritzBox versions are supported. During startup there are messages about disabled services.
This is normal as there are values not available on certain models.

### Environment
* Grafana >= 8.4.0

## Setup
* here we assume we install in `/opt`

### Configuration

After cloning the repo copy the config from the [example](fritzinfluxdb-sample.ini)
to ```fritzinfluxdb.ini``` and edit the settings. All settings are described inside the file.

#### Environment variables

Config values can also be overwritten using environment variables.<br>
schema: <SECTION_NAME>_<CONFIG_OPTION> (all in capital letters)<br>
example for InfluxDB token:<br>
`export INFLUXDB_TOKEN="abcedef"`

Environment variables will overwrite options defined in config file.

### Installation
<details>
    <summary>Ubuntu</summary>

```shell
sudo apt-get install python3-virtualenv
cd /opt
git clone https://github.com/yunity/fritzinfluxdb.git
cd fritzinfluxdb
virtualenv -p python3 .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```
</details>
<details>
    <summary>RHEL/CentOS 7 with EPEL</summary>

```shell
yum install git python36-virtualenv
cd /opt
git clone https://github.com/yunity/fritzinfluxdb.git
cd fritzinfluxdb
virtualenv-3 .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```
</details>
<details>
    <summary>RHEL/Rocky/Alma 8</summary>

```shell
dnf install git-core python3-virtualenv
cd /opt
git clone https://github.com/yunity/fritzinfluxdb.git
cd fritzinfluxdb
virtualenv-3 .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```
</details>
<details>
    <summary>RHEL/Rocky/Alma 9</summary>

```shell
dnf install git-core
cd /opt
git clone https://github.com/yunity/fritzinfluxdb.git
cd fritzinfluxdb
python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```
</details>

* modify your configuration and test it
```
./fritzinfluxdb.py
```

#### Install as systemd service
Ubuntu
```
cp /opt/fritzinfluxdb/fritzinfluxdb.service /etc/systemd/system
```
RHEL/CentOS/Rocky/Alma
```
sed -e 's/nogroup/nobody/g' /opt/fritzinfluxdb/fritzinfluxdb.service > /etc/systemd/system/fritzinfluxdb.service
```

```
systemctl daemon-reload
systemctl start fritzinfluxdb
systemctl enable fritzinfluxdb
```

### Docker

Run the application in a docker container. You can build it yourself or use the ones from docker hub.

Available here: [bbricardo/fritzinfluxdb](https://hub.docker.com/r/bbricardo/fritzinfluxdb)

* The application working directory is ```/app```

To build it by yourself just run:
```shell
docker build -t bbricardo/fritzinfluxdb:latest .
```

To start the container just use:
```shell
docker run --rm -d -v /PATH/TO/fritzinfluxdb.ini:/app/fritzinfluxdb.ini --name fritzinfluxdb bbricardo/fritzinfluxdb:latest
```

You can alternatively use the provided [docker-compose.yml](docker-compose.yml):
```
docker-compose up -d
```
If you're running the influxdb in a docker on the same host you need to add `--link` to the run command.

### Example:
* starting the influx container
```
docker run --name=influxdb -d -p 8086:8086 influxdb
```
* set influxdb host in `fritzinfluxdb.ini` to `influxdb`
* run docker container
```
docker run --link influxdb -d -v /PATH/TO/fritzinfluxdb.ini:/app/fritzinfluxdb.ini --name fritzinfluxdb fritzinfluxdb
```

### Upgrading

* update your virtual env `pip3 install -r requirements.txt`
* use the updated config and add the credentials and addresses from your old config

### InfluxDB Setup

To create an InfluxDB 1 database or InfluxDB 2 Bucket (incl. retention policy mapping) it is recommended to use
admin credentials/token on the first run. **DON'T** use an admin token after initial setup has finished.

InfluxDB 1 example:
```shell
export INFLUXDB_USERNAME=admin
export INFLUXDB_PASSWORD=SuperSecret
```

InfluxDB 2 example:
```shell
export INFLUXDB_TOKEN=InfluxDBAdminToken
```

If running via docker [this](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file)
link describes how to set env vars on a `docker run`

For InfluxDB 2 it is highly recommended creating a specific write only token for the defined bucket.

### Setup InfluxDB 2 datasource in Grafana for fritzinfluxdb

The Grafana Dashboard is build using the InfluxQL query language. Therefore, the definition of the InfluxDB datasource
in Grafana needs to be adopted.

As "Query Language" define: InfluxQL<br>
Set the http url to your InfluxDB instance

Now "Add header":<br>
* Header: Authorization
* Value: Token {API_TOKEN}

Here substitute `{API_TOKEN}` with your read token for the InfluxDB 2 bucket.

The last option would be the database which is the same as the bucket defined in your config.

See this comment for details: https://github.com/karrot-dev/fritzinfluxdb/issues/18#issuecomment-1073066993

## Running the script
```
usage: fritzinfluxdb.py [-h] [-c fritzinfluxdb.ini [fritzinfluxdb.ini ...]] [-d] [-v]

fritzinfluxdb
Version: 1.0.0 (2022-06-11)
Project URL: https://github.com/karrot-dev/fritzinfluxdb

optional arguments:
  -h, --help            show this help message and exit
  -c fritzinfluxdb.ini [fritzinfluxdb.ini ...], --config fritzinfluxdb.ini [fritzinfluxdb.ini ...]
                        points to the config file to read config data from which is not installed under the default path './fritzinfluxdb.ini'
  -d, --daemon          define if the script is run as a systemd daemon
  -v, --verbose         turn on verbose output to get debug logging. Defining '-vv' will also print out all http calls
```

## Grafana

There are following Dashboards included:
* [fritzbox_system_dashboard.json](grafana/fritzbox_system_dashboard.json)
* [fritzbox_logs_dashboard.json](grafana/fritzbox_logs_dashboard.json)

*This was heavily inspired from: https://grafana.com/dashboards/713*

## Configure more attributes

check here to find an overview of more attributes which probably could be added
https://wiki.fhem.de/w/index.php?title=FRITZBOX

New TR-069 services can be defined in [fritzinfluxdb/classes/fritzbox/services_tr069.py](fritzinfluxdb/classes/fritzbox/services_tr069.py)
New LUA services can be defined in [fritzinfluxdb/classes/fritzbox/services_lua.py](fritzinfluxdb/classes/fritzbox/services_lua.py)

# License
>You can check out the full license [here](LICENSE.txt)

This project is licensed under the terms of the **MIT** license.
