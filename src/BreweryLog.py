# system imports
from time import sleep
import argparse
import threading
import socket
import json

# Influx db imports
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# DEBUG LEVEL
DEBUG = 1

# socket connection information
server_ip = "ashinkl-rpiz2w"
server_port = 12345

# socket connection information (outside)
outside_server_ip = "ashinkl-rpipw"
outside_server_port = 12345

# TEST
socket_err_cnt = 0

# db information (test for now)
# hostname and port 127.0.0.1:8086
USER = 'ashinkl'
PASSWORD = 'ashinkl123'
BUCKET = 'OstentatiousBrewing'
INFLUXDB_API_TOKEN = 'l8yvgryXx262i3ilLlDo4CTaxOJPPfFaAtvuU7w8_Pm6BCyAV-LeDqLC4BO9qDPZPzlTtHPUcxFHWF21tKVx2Q=='
INFLUXDB_ORG = 'home'
DB_WRITE_FREQ = 60
GET_SENSOR_DATA_FREQ = 55

# global variables to communicate between threads
terminate_thread = 0
new_data_avail = False
new_outside_data_avail = False

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
			
			if DEBUG > 2:
				print("Received from server:", data.decode())
			
			# get sensor data from server
			sensor_data = json.loads(data.decode())

			if DEBUG > 1:
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

			client_socket.close()

			# inform the other thread new data is available
			new_data_avail = True

		except socket.gaierror:
			socket_err_cnt += 1
			print(f"Socket Error Number: {socket_err_cnt}")
			terminate_thread = True ##DEFUGGING ONLY

		except ConnectionRefusedError:
			print("Cannot connect to server...will try again later.")
		
		finally:
			sleep(GET_SENSOR_DATA_FREQ)

# function that gets the values of the data
# and stores the values in global variables
# designed to be run in a thread 
def get_outside_sensor_data():
	
	global terminate_thread
	global outside_temp
	global outside_pressure
	global outside_humidity
	global new_outside_data_avail
	
	while not terminate_thread:
		
		print("Running Thread: get_outside_sensor_data")
		
		try:
			# connect to the server which has the data
			client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			client_socket.settimeout(60)
			client_socket.connect((outside_server_ip,outside_server_port))

			# get the data from the socket
			data = client_socket.recv(1024)
			
			if DEBUG > 2:
				print("Received from server:", data.decode())
			
			# get sensor data from server
			outside_sensor_data = json.loads(data.decode())
			
			# parse dictionary data
			# dictionary elements: 
				# Temperature_CRunning Thread: get_sensor_data
				# RelativePressure_hPa
				# Humidity_%
				
			if DEBUG > 1:
				print(outside_sensor_data)

			outside_temp = outside_sensor_data["Temperature_C"]
			outside_temp = round((9 * float(outside_temp))/5  + 32,1)
			outside_pressure = outside_sensor_data["RelativePressure_hPa"]
			outside_humidity = outside_sensor_data["Humidity_%"]

			client_socket.close()

			# inform the other thread new data is available
			new_outside_data_avail = True

		except socket.gaierror:
			socket_err_cnt += 1
			print(f"Socket Error Number: {socket_err_cnt}")

		except ConnectionRefusedError:
			print("Cannot connect to server...will try again later.")

		except socket.Timeouterror:
			print("Cannot connect to server (timeout)...will try again later.")
		
		finally:
			sleep(GET_SENSOR_DATA_FREQ)

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
	global outside_temp
	global outside_pressure
	global outside_humidity
	global new_data_avail
	global new_outside_data_avail
	
	while not terminate_thread:
		
		print("Running Thread: write_data_to_db")

		try:

			# only write data if it is not stale
			if new_data_avail:

				print("Writing values to database...")

				# create a point and write it to the database - Fermentation Chamber Temperature 1
				p = Point("Fermentation Chamber").tag("location", "Chamber 1").field("temperature", fermentation_chamber_temp_1)
				write_api.write(bucket=BUCKET, record=p)	

				# create a point and write it to the database - Fermentation Chamber Temperature 2
				p = Point("Fermentation Chamber").tag("location", "Chamber 2").field("temperature", fermentation_chamber_temp_2)
				write_api.write(bucket=BUCKET, record=p)

				# set the data to stale
				new_data_avail = False

			# only write data if it is not stale
			if new_outside_data_avail:

				print("Writing outside values to database...")

				# create a point and write it to the database - Outside Temperature
				p = Point("Outside").tag("location", "Patio").field("temperature", outside_temp)
				write_api.write(bucket=BUCKET, record=p)

				# create a point and write it to the database - Outside Pressure
				p = Point("Outside").tag("location", "Patio").field("pressure", outside_pressure)
				write_api.write(bucket=BUCKET, record=p)

				# create a point and write it to the database - Outside Humidity
				p = Point("Outside").tag("location", "Patio").field("humidity", outside_humidity)
				write_api.write(bucket=BUCKET, record=p)	

				# set the data to stale
				new_outside_data_avail = False

		except ConnectionRefusedError:
			print("Cannot connect to server...will try again later.")
		
		finally:
			sleep(DB_WRITE_FREQ)



# main program
try:

	client = InfluxDBClient(url="http://localhost:8086", token=INFLUXDB_API_TOKEN, org='home')
	#client = InfluxDBClient.from_config_file("influx_db_config.ini") --> fix this...

	# create the apis to send data to the database
	write_api = client.write_api(write_options=SYNCHRONOUS)
	query_api = client.query_api()
	
	# create the thread to get the information from the server
	thread_get_sensor_data = threading.Thread(target=get_sensor_data)
	thread_get_sensor_data.start()	

	# create the thread to get the information from the outsude server
	thread_get_outside_sensor_data = threading.Thread(target=get_outside_sensor_data)
	thread_get_outside_sensor_data.start()	

	# create the thread to write the information to the database
	thread_write_data_to_db = threading.Thread(target=write_data_to_db)
	thread_write_data_to_db.start()

	# keep the threads alive and restarts them if they crash
	while True:


		if not thread_get_sensor_data.is_alive():

			thread_get_sensor_data = threading.Thread(target=get_sensor_data)
			thread_get_sensor_data.start()	

		if not thread_get_outside_sensor_data.is_alive():

			thread_get_outside_sensor_data = threading.Thread(target=get_outside_sensor_data)
			thread_get_outside_sensor_data.start()	

		if not thread_write_data_to_db.is_alive():
			
			thread_write_data_to_db = threading.Thread(target=write_data_to_db)
			thread_write_data_to_db.start()

		sleep(10)

except KeyboardInterrupt:
	terminate_thread = 1
	thread_get_sensor_data.join
	thread_get_outside_sensor_data.join
	thread_write_data_to_db.join

finally:
	print("Script terminated!")
	print(f"Socket Error Count: {socket_err_cnt}")