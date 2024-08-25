import argparse

# system imports
from time import sleep
import threading
import socket
import json

import math
from datetime import datetime
import time

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from ISOtime import get_current_iso_time

# DEBUG LEVEL
DEBUG = 1

# socket connection information
server_ip = "ashinkl-rpiz2w"
server_port = 12345

# db information (test for now)
USER = 'ashinkl'
PASSWORD = 'ashinkl123'
DBNAME = 'TestDB'
BUCKET = 'OstentatiousBrewing'
INFLUXDB_API_TOKEN = 'l8yvgryXx262i3ilLlDo4CTaxOJPPfFaAtvuU7w8_Pm6BCyAV-LeDqLC4BO9qDPZPzlTtHPUcxFHWF21tKVx2Q=='

host = "127.0.0.1" #check this
port = 8086 #check this

# global variables to communicate between threads
terminate_thread = 0
new_data_avail = False

# function that gets the values of the data
# and stores the values in global variables
# designed to be run in a thread 
def get_sensor_data():
	
	global terminate_thread
	global keg_level_1
	global keg_level_2
	global fermentation_chamber_temp_1
	global fermentation_chamber_temp_2
	global kegerator_temp
	global new_data_avail
	
	while not terminate_thread:
		

		print("Running Thread: get_sensor_data")
		
		try:
			# connect to the server which has the data
			client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			client_socket.connect((server_ip,server_port))

			# get the data from the socket
			data = client_socket.recv(1024)
			
			if DEBUG > 0:
				print("Received from server:", data.decode())
			
			# get sensor data from server
			sensor_data = json.loads(data.decode())
			
			if DEBUG > 0:
				print(sensor_data)
			
			# parse dictionary data
			# dictionary elements: 
				# FermentationChamberTemp1_F
				# FermentationChamberTemp2_F
				# KegeratorTemp_F
				# KegWeightSensor1_PCT
				# KegWeightSensor2_PCT

			keg_level_1 = sensor_data["KegWeightSensor1_PCT"]
			keg_level_2 = sensor_data["KegWeightSensor2_PCT"]
			fermentation_chamber_temp_1 = sensor_data["FermentationChamberTemp1_F"]
			fermentation_chamber_temp_2 = sensor_data["FermentationChamberTemp2_F"]
			kegerator_temp = sensor_data["KegeratorTemp_F"]

			new_data_avail = True

			client_socket.close()

		except ConnectionRefusedError:
			print("Cannot connect to server...will try again later.")
		
		finally:
			sleep(1)

# function that get the received
# values from the global variables
# and writes them to an influx db
# designed to be run in a thread 
def write_data_to_db():
	
	global terminate_thread
	global keg_level_1
	global keg_level_2
	global fermentation_chamber_temp_1
	global fermentation_chamber_temp_2
	global kegerator_temp
	global new_data_avail
	
	while not terminate_thread:
		
		print("Running Thread: write_data_to_db")

		try:

		
			if new_data_avail:
				
				# Write points
				#client.write_points(points) sensor_data["KegeratorTemp_F"]

				p = Point("Fermentation Chamber").tag("location", "Chamber 1").field("temperature", fermentation_chamber_temp_1)
				write_api.write(bucket=BUCKET, record=p)	

				p = Point("Fermentation Chamber").tag("location", "Chamber 2").field("temperature", fermentation_chamber_temp_2)
				write_api.write(bucket=BUCKET, record=p)

				new_data_avail = False



		except ConnectionRefusedError:
			print("Cannot connect to server...will try again later.")
		
		finally:
			sleep(30)



# main program
try:

	client = InfluxDBClient(url="http://localhost:8086", token=INFLUXDB_API_TOKEN, org='home')
	#client = InfluxDBClient.from_config_file("influx_db_config.ini") --> fix this...

	write_api = client.write_api(write_options=SYNCHRONOUS)
	query_api = client.query_api()
	
	# start the thread to get the information from the server
	thread_get_sensor_data = threading.Thread(target=get_sensor_data)
	thread_get_sensor_data.start()	

	# start the thread to get the information from the server
	thread_write_data_to_db = threading.Thread(target=write_data_to_db)
	thread_write_data_to_db.start()


	sleep(10)

	terminate_thread = 1

finally:
	print("Script terminated!")