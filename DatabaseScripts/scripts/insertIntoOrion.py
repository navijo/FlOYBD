
import pyspark
import os.path
import time
from pyspark import SparkContext,SparkConf

from pyspark.sql import SQLContext
from pyspark.sql.functions import count
from collections import defaultdict
import requests
import json
import sys
import getopt
from cassandra.cluster import Cluster
from cassandra.query import named_tuple_factory

def initEnvironment():
	global sc,sql
	conf = SparkConf()
	spark_home = os.environ.get('SPARK_HOME', None)
	conf.setMaster("spark://192.168.246.236:7077")
	conf.setAppName("Orion Insert")
	conf.set("spark.cassandra.connection.host","192.168.246.236")
	conf.set("spark.executor.memory", "10g")
	#conf.set("spark.driver.memory", "15g")
	conf.set("spark.num.executors","2")

	sc = SparkContext(conf=conf)
	sql = SQLContext(sc)

def sendStationsToOrion(orionIp):
	
	stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")

	pandas_df = stations.toPandas()
	stationsJson = pandas_df.to_json(orient='records',path_or_buf = None)
	stationsJsonObject = json.loads(stationsJson)

	for station in stationsJsonObject:
		stationData = {}
		station_id = station["station_id"]
		name = station["name"]
		latitude = station["latitude"]
		longitude = station["longitude"]
		altitude = station["altitude"]
		indsinop = station["indsinop"]
		province = station["province"]

		location = {}
		point = {}
		point["type"] = "Point"
		point["coordinates"] =  [float(latitude),float(longitude)]
		location["type"] = "geo:json"
		location["value"] = point
		stationData["location"] = location
		
		stationData["id"] = station_id
		stationData["type"] = "Station"
		nameJson = {}
		nameJson["value"] = name
		nameJson["type"] = "string"
		stationData["name"] =  nameJson

		indisinopJson = {}
		indisinopJson["value"] = indsinop
		indisinopJson["type"] = "string"
		stationData["indsinop"] =  indisinopJson

		provinceJson = {}
		provinceJson["value"] = province
		provinceJson["type"] = "string"
		stationData["province"] =  provinceJson
	
		print (json.dumps(stationData))
		
		response = requests.post(orionIp+":1026/v2/entities", 
			headers = {'Accept': 'application/json','Content-Type': 'application/json','Fiware-Service': 'gsoc17_floybd','Fiware-ServicePath': '/measurements'},
			data = json.dumps(stationData))
		print(response)
		print(response.text)
		#break

def sendMeasurementsToOrion(orionIp):
	cluster = Cluster(['192.168.246.236'])
	session = cluster.connect("dev")
	session.row_factory = named_tuple_factory

	clean_daily = session.execute("Select * from clean_daily_measurement;",timeout=100000)
	
	counter = 1

	for measure in clean_daily:
		measureData = {}
		station_id = str(measure[0])
		measure_date = str(measure[1]) 
		insolation = float(measure[2]) if measure[2] is not None else 0
		#max_press_hour = measure[3]
		max_pressure =  float(measure[4]) if measure[4] is not None else 0
		max_temp =  float(measure[5]) if measure[5] is not None else 0
		#max_temp_hour = measure[6]
		med_temp =  float(measure[7]) if measure[7] is not None else 0
		#min_press_hour = measure[8]
		min_pressure =  float(measure[9]) if measure[9] is not None else 0
		min_temp =  float(measure[10]) if measure[10] is not None else 0
		#min_temp_hour = measure[11]
		precip =  float(measure[12]) if measure[12] is not None else 0
		#wind_dir = measure[13]
		wind_med_vel =  float(measure[14]) if measure[14] is not None else 0
		#wind_streak = measure[15]
		#wind_streak_hour = measure[16]

		
		measureData["id"] = str(station_id)+"-"+str(measure_date)
		measureData["type"] = "Measurement"
		
		dateJson = {}
		dateJson["value"] = measure_date
		dateJson["type"] = "date"
		measureData["date"] =  dateJson

		insolationJson = {}
		insolationJson["value"] = insolation
		insolationJson["type"] = "float"
		measureData["insolation"] =  insolationJson

		maxPressureJson = {}
		maxPressureJson["value"] = max_pressure
		maxPressureJson["type"] = "float"
		measureData["max_pressure"] =  maxPressureJson

		minPressureJson = {}
		minPressureJson["value"] = min_pressure
		minPressureJson["type"] = "float"
		measureData["min_pressure"] =  minPressureJson

		maxTempJson = {}
		maxTempJson["value"] = max_temp
		maxTempJson["type"] = "float"
		measureData["max_temp"] =  maxTempJson

		medTempJson = {}
		medTempJson["value"] = med_temp
		medTempJson["type"] = "float"
		measureData["med_temp"] =  medTempJson

		minTempJson = {}
		minTempJson["value"] = min_temp
		minTempJson["type"] = "float"
		measureData["min_temp"] =  minTempJson

		minTempJson = {}
		minTempJson["value"] = min_temp
		minTempJson["type"] = "float"
		measureData["min_temp"] =  minTempJson

		precipJson = {}
		precipJson["value"] = precip
		precipJson["type"] = "float"
		measureData["precip"] =  precipJson

		windMedVelJson = {}
		windMedVelJson["value"] = wind_med_vel
		windMedVelJson["type"] = "float"
		measureData["wind_med_vel"] =  windMedVelJson

		payload =json.dumps(measureData)

		response = requests.post(orionIp+":1026/v2/entities", 
			headers = {'Accept': 'application/json','Content-Type': 'application/json','Fiware-Service': 'gsoc17_floybd','Fiware-ServicePath': '/measurements'},
			data = payload)
		
		print(str(counter) +"\t" + str(measureData["id"]) + " : " + str(response) + "==>" + str(response.text))
		counter +=1

def sendEarthquakesToOrion(orionIp):
	
	cluster = Cluster(['192.168.246.236'])
	session = cluster.connect("dev")
	session.row_factory = named_tuple_factory

	earthquakes = session.execute("Select * from earthquake;",timeout=100000)

	counter = 1

	for earthquake in earthquakes:
		earthquakeData = {}

		eventId = str(earthquake[0])
		depth = float(earthquake[1]) if earthquake[1] is not None else 0
		fecha = str(earthquake[2].strftime('%Y/%m/%d'))

		latitude = float(earthquake[3]) if earthquake[3] is not None else 0
		longitude = float(earthquake[4]) if earthquake[4] is not None else 0
		magnitude = float(earthquake[5]) if earthquake[5] is not None else 0
		place = str(earthquake[6]) if earthquake[6] is not None else 0
		time = float(earthquake[7]) if earthquake[7] is not None else 0

		earthquakeData["id"] = str(eventId)
		earthquakeData["type"] = "Earthquake"

		depthJson = {}
		depthJson["value"] = depth
		depthJson["type"] = "float"
		earthquakeData["depth"] =  depthJson

		fechaJson = {}
		fechaJson["value"] = fecha
		fechaJson["type"] = "date"
		earthquakeData["fecha"] =  fechaJson

		latitudeJson = {}
		latitudeJson["value"] = latitude
		latitudeJson["type"] = "float"
		earthquakeData["latitude"] =  latitudeJson

		longitudeJson = {}
		longitudeJson["value"] = longitude
		longitudeJson["type"] = "float"
		earthquakeData["longitude"] =  longitudeJson

		placeJson = {}
		placeJson["value"] = place
		placeJson["type"] = "string"
		earthquakeData["place"] =  placeJson

		magnitudeJson = {}
		magnitudeJson["value"] = magnitude
		magnitudeJson["type"] = "float"
		earthquakeData["magnitude"] =  magnitudeJson

		timeJson = {}
		timeJson["value"] = time
		timeJson["type"] = "float"
		earthquakeData["time"] =  timeJson

		payload =json.dumps(earthquakeData)
		
		response = requests.post(orionIp+":1026/v2/entities", 
			headers = {'Accept': 'application/json','Content-Type': 'application/json','Fiware-Service': 'gsoc17_floybd','Fiware-ServicePath': '/measurements'},
			data = payload)
		
		print(str(counter) +"\t" +str(earthquakeData["id"]) + " : " + str(response) + "==>" + str(response.text))
		counter +=1


def main(argv):
	global sc,sql
	#orionIp = "http://130.206.121.247"
	orionIp = "http://192.168.249.136"
	typeS = ''
	try:
		opts, args = getopt.getopt(argv, "ht:", ["help", "type="])
		if not opts or len(opts) < 1:
			usage()
			sys.exit(2)
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit()
		elif opt in ("-t", "--type"):
			typeS = arg
	print ('Type ', typeS)

	if typeS == 'stations':
		print("Stations")
		initEnvironment()
		sendStationsToOrion(orionIp)
		sc.stop()
	elif typeS == 'measurements':
		print("Measurements")
		#initEnvironment()
		sendMeasurementsToOrion(orionIp)
	elif typeS == 'earthquakes':
		print("Earthquakes")
		#initEnvironment()
		sendEarthquakesToOrion(orionIp)


def usage():
	print ('Usage=> insertIntoOrion.py -t <stations/measurements/earthquakes>')


if __name__ == "__main__":

	start_time = time.time()
	main(sys.argv[1:])
	
	print("--- %s seconds ---" % (time.time() - start_time))
	print("END")
