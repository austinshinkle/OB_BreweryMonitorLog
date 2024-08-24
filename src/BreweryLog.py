import argparse

# system imports
from time import sleep
import threading
import socket
import json

import math
from datetime import datetime
import time

from influxdb import InfluxDBClient
from ISOtime import get_current_iso_time

# DEBUG LEVEL
DEBUG = 1

# socket connection information
server_ip = "ashinkl-rpiz2w"
server_port = 12345

# db information (test for now)
USER = 'admin'
PASSWORD = 'admin'
DBNAME = 'TestDB'

host = "127.0.0.1" #check this
port = 8086 #check this

# global variables to communicate between threads
terminate_thread = 0

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
	
	while not terminate_thread:
		
		
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

			# Write points
			#client.write_points(points) sensor_data["KegeratorTemp_F"]

			client_socket.close()
		
		except ConnectionRefusedError:
			print("Cannot connect to server...will try again later.")
		
		finally:
			sleep(1)

# main program
try:

	# start the thread to get the information from the server
	thread_get_sensor_data = threading.Thread(target=get_sensor_data)
	thread_get_sensor_data.start()


	client = InfluxDBClient(host, port, USER, PASSWORD, DBNAME)

	print("Create database: " + DBNAME)
	client.create_database(DBNAME)
	client.switch_database(DBNAME)


	sleep(10)
	# Write points
	#client.write_points(points)

	terminate_thread = 1

finally:
	print("Script terminated!")