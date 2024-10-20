# system imports
from time import sleep
import argparse
import threading
import socket
import json

from paho.mqtt import client as mqtt_client


# DEBUG LEVEL
DEBUG = 1

# socket connection information
server_ip = "ashinkl-rpiz2w"
server_port = 12345

# socket connection information (outside)
outside_server_ip = "ashinkl-rpipw"
outside_server_port = 12345

# defines to determine how long to wait to write data
GET_SENSOR_DATA_FREQ = 15 #55
MQTT_WRITE_FREQ = 20 #60


broker = 'homeassistant.local'
port = 1883
topic_inside_temp = "/home/inside/temperature"
topic_outside_temp = "/home/outside/temperature"
topic_outside_humidity = "/home/outside/humidity"
client_id = f'python-mqtt-555'
username = 'mqtt-user'

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

# function that creates and starts the mqtt connection
def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):

        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)

    client.username_pw_set(username, username)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


# function that get the received
# values from the global variables
# and writes them to an MQTT broker
# designed to be run in a thread 
def write_data_to_mqtt():
	
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
		
		print("Running Thread: write_data_to_mqtt")

		try:

			# only write data if it is not stale
			if new_data_avail:

				if DEBUG > 1:
					print("Writing values to MQTT...")
				
				result = client.publish(topic_inside_temp, str(fermentation_chamber_temp_1)) 
		
				# set the data to stale
				new_data_avail = False

			# only write data if it is not stale
			if new_outside_data_avail:

				if DEBUG > 1:
					print("Writing outside values to MQTT...")

				result = client.publish(topic_outside_temp, str(outside_temp)) 
				result = client.publish(topic_outside_humidity, str(outside_humidity)) 

				# set the data to stale
				new_outside_data_avail = False

		except ConnectionRefusedError:
			print("Cannot connect to server...will try again later.")
		
		finally:
			sleep(MQTT_WRITE_FREQ)



# main program
try:

    client = connect_mqtt()
	
	# create the thread to get the information from the server
    thread_get_sensor_data = threading.Thread(target=get_sensor_data)
    thread_get_sensor_data.start()	

	# create the thread to get the information from the outsude server
    thread_get_outside_sensor_data = threading.Thread(target=get_outside_sensor_data)
    thread_get_outside_sensor_data.start()	

	# create the thread to write the information to the database
    thread_write_data_to_mqtt = threading.Thread(target=write_data_to_mqtt)
    thread_write_data_to_mqtt.start()

	# keep the threads alive and restarts them if they crash
    while True:


        if not thread_get_sensor_data.is_alive():

            thread_get_sensor_data = threading.Thread(target=get_sensor_data)
            thread_get_sensor_data.start()	

        if not thread_get_outside_sensor_data.is_alive():

            thread_get_outside_sensor_data = threading.Thread(target=get_outside_sensor_data)
            thread_get_outside_sensor_data.start()	

        if not thread_write_data_to_mqtt.is_alive():
			
            thread_write_data_to_mqtt = threading.Thread(target=write_data_to_mqtt)
            thread_write_data_to_mqtt.start()

        sleep(10)

except KeyboardInterrupt:
	terminate_thread = 1
	thread_get_sensor_data.join
	thread_get_outside_sensor_data.join
#	thread_write_data_to_db.join

finally:
	print("Script terminated!")