# OB_BreweryMonitorLog

### Install InfluxDB v1 by following these instructions
https://pimylifeup.com/raspberry-pi-influxdb/

### Install Grafana by following these instructions
https://grafana.com/tutorials/install-grafana-on-raspberry-pi/

### Used this as a reference as well to connect InfluxDB to Grafana
https://sandyjmacdonald.github.io/2021/12/29/setting-up-influxdb-and-grafana-on-the-raspberry-pi-4/

### Python code uses this repository
https://github.com/influxdata/influxdb-python
Install the library on Raspberry Pi using this command
```
sudo apt install python3-influxdb
```


```
> SELECT value FROM temperature
name: temperature
time                value
----                -----
1718735181233678885 65
1718735189609397142 80
1718735194185828797 25
1718735200258097674 55
```
