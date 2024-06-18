import argparse

import math
import datetime
import time

from influxdb import InfluxDBClient

USER = 'admin'
PASSWORD = 'admin'
DBNAME = 'BreweryLog'

host = 127.0.0.1 #check this
port = 8086 #check this

client = InfluxDBClient(host, port, USER, PASSWORD, DBNAME)

print("Create database: " + DBNAME)
client.create_database(DBNAME)
client.switch_database(DBNAME)
