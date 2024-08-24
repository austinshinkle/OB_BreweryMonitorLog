import time

DEBUG = 0

def get_current_iso_time():

	# get and print the current local time
	current_time_ascii = time.asctime()
	print(current_time_ascii)	
	current_time = time.localtime()

	# parse the local time into ISO 8601 format
	# year
	iso_time = str(current_time.tm_year) + "-" 

	# month
	if current_time.tm_mon < 10:
		iso_time += "0" + str(current_time.tm_mon) + "-" 
	else:
		iso_time += str(current_time.tm_mon) + "-" 

	# day
	if current_time.tm_mday < 10:
		iso_time += "0" + str(current_time.tm_mday) + "T" 
	else:
		iso_time += str(current_time.tm_mday) + "T" 
		
	# hour
	if current_time.tm_hour < 10:
		iso_time += "0" + str(current_time.tm_hour) + ":" 
	else:
		iso_time += str(current_time.tm_hour) + ":" 

	# minute
	if current_time.tm_min < 10:
		iso_time += "0" + str(current_time.tm_min) + ":" 
	else:
		iso_time += str(current_time.tm_min) + ":" 
		
	# seconds
	if current_time.tm_sec < 10:
		iso_time += "0" + str(current_time.tm_sec) 
	else:
		iso_time += str(current_time.tm_sec)
		
	if DEBUG:
		print(iso_time) 
	return iso_time