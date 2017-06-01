from flask import Flask
from flask import send_from_directory
from flask import request
from pyspark import SparkContext,SparkConf
from pyspark.sql import SQLContext, SparkSession

import os.path
import sys
import time
import json

import datetime
import functools
from utils import sparkFunctions, generalFunctions

from flask import jsonify

app = Flask(__name__, static_url_path='')

def timing(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsedTime * 1000)))
    return newfunc


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/get')
def get():
     return send_from_directory(directory='.', filename='cylinders_weather1492600389.kml',as_attachment=True,
        mimetype='application/octet-stream')


@app.route('/saveAPIKey', methods=['POST'])
def saveApiKey():
	creation_date=request.form['date']
	apiKey=request.form['apiKey']
	generalFunctions.saveKEY(creation_date,apiKey)


@app.route('/saveAPIKeyGet', methods=['GET'])
def saveApiKeyGet():
	apiKey=request.args.get('key')
	creation_date = datetime.datetime.now()
	generalFunctions.saveKEY(creation_date,apiKey)


@app.route('/getKey', methods=['GET'])
def getApiKey():
	return generalFunctions.getKey()


@app.route('/getAllStationsMeasurementsKML')
def getAllStationsMeasurementsKML():
	initEnvironment()
	loadStations()
	loadCleanDaily()
	date = request.args.get('date')
	weatherData = sparkFunctions.getConcreteWeatherData(clean_daily,'',date,"True")

	timestamp =  time.time()
	fileName = "measurement_"+str(int(timestamp))
	generalFunctions.generateAllStationsKml(weatherData,stations,fileName)

	stopEnvironment(sc)
	return send_from_directory(directory='.', filename="kmls/"+fileName+".kml",as_attachment=True,mimetype='application/octet-stream')

@app.route('/getMeasurementKml')
def getMeasurementKml(): 
	initEnvironment()
	loadStations()
	loadCleanDaily()

	date = request.args.get('date')
	station_id = request.args.get('station_id')

	weatherData = sparkFunctions.getConcreteWeatherData(clean_daily,station_id,date,"False")
	stationData = sparkFunctions.getStationInfo(stations,station_id)
	
	timestamp =  time.time()
	fileName = "measurement_"+str(int(timestamp))
	
	generalFunctions.generateKml(weatherData,stationData,fileName)
	stopEnvironment(sc)
	return send_from_directory(directory='.', filename="kmls/"+fileName+".kml",as_attachment=True,mimetype='application/octet-stream')


@app.route('/getMeasurement')
def getMeasurement(): 
	initEnvironment()
	loadCleanDaily()
	date = request.args.get('date')
	station_id = request.args.get('station_id')
	getAllStations = request.args.get('allStations')

	weatherData = sparkFunctions.getConcreteWeatherData(clean_daily,station_id,date,getAllStations)
	weatherJson = generalFunctions.dataFrameToJsonStr(weatherData)

	stopEnvironment(sc)
	return jsonify(weatherJson)



@timing
@app.route('/getEarthquakes')
def getEarthquakes(): 
	initEnvironment()
	loadEarthquakes()
	date = request.args.get('date')
	max_lat = request.args.get('max_lat')
	min_lat = request.args.get('min_lat')
	max_lon = request.args.get('max_lon')
	min_lon = request.args.get('min_lon')

	earthquakesData = sparkFunctions.getConcreteEarhquakesData(earthquakes,date,max_lat,min_lat,max_lon,min_lon)
	earthquakesJson = generalFunctions.dataFrameToJsonStr(earthquakesData)
	#earthquakesJson = earthquakesData

	stopEnvironment(sc)
	return jsonify(earthquakesJson)


@app.route('/getPrediction',methods=['POST'])
def getPrediction(): 

	data = request.data
	dataStr = str(data,'utf-8')
	dataDict = json.loads(dataStr)
	initEnvironment()

	station_id = dataDict["station_id"]
	columns = dataDict['columnsToPredict']

	#try:
	stationData = sparkFunctions.getStationInfo(stations,station_id)
	currentWeather = generalFunctions.getCurrentWeather(station_id)
	if(currentWeather!=0):
		weatherPrediction = sparkFunctions.predict(sql,sc,columns,station_id,currentWeather)
		if(weatherPrediction):
			predictionJson = weatherPrediction
			#predictionJson = generalFunctions.dataFrameToJsonStr(weatherPrediction)
		else:
			predictionJson = "No Model"
		stopEnvironment()
		print(predictionJson)
		return jsonify(predictionJson)
	else:
		return "No Current Weather"
	#except:
	#	print("Unexpected error:", sys.exc_info()[0])
	stopEnvironment(sc)


@app.route('/getAllStations')
def getAllStations(): 
	initEnvironment()
	loadStations()
	
	timestamp =  time.time()
	fileName = "measurement_"+str(int(timestamp))
	stationsJson = generalFunctions.dataFrameToJsonStr(stations)
	stopEnvironment(sc)
	return stationsJson


@app.route('/getStats',methods=['POST'])
def getStats():
	initEnvironment()

	data = request.data
	dataStr = str(data,'utf-8')
	dataDict = json.loads(dataStr)

	allStations = dataDict['allStations']
	allTime = dataDict['allTime']
	dateFrom = dataDict['dateFrom']
	dateTo = dataDict['dateTo']
	station_id = dataDict['station_id']

	try:
		if allTime:
			loadGlobalWeatherStats()
			if allStations:
				returnJson = generalFunctions.dataFrameToJsonStr(stations_limits)
				stopEnvironment(sc)
				return jsonify(returnJson)
			else:
				tmpDf = sparkFunctions.getLimitsForStation(stations_limits,station_id)
				returnJson = generalFunctions.dataFrameToJsonStr(tmpDf)
				stopEnvironment(sc)
				return jsonify(returnJson)
		else:
			loadCleanDaily()
			if(allStations):
				tmpDf = sparkFunctions.getLimitsAllStationsWithInterval(clean_daily,dateFrom,dateTo)
				returnJson = generalFunctions.dataFrameToJsonStr(tmpDf)
				stopEnvironment(sc)
				return jsonify(returnJson)
			else:
				tmpDf = sparkFunctions.getLimitsStationWithInterval(clean_daily,station_id,dateFrom,dateTo)
				returnJson = generalFunctions.dataFrameToJsonStr(tmpDf)
				stopEnvironment(sc)
				return jsonify(returnJson)
	except:
		print("Ooops, something went wrong getting the stats")
		stopEnvironment(sc)
	


def loadGlobalWeatherStats():
	global stations_limits
	stations_limits =  sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station_limits")


def loadStations():
	global stations
	stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")


def loadCleanDaily():
	global clean_daily
	clean_daily = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="clean_daily_measurement")

def loadEarthquakes():
	global earthquakes
	earthquakes = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="earthquake")



def initEnvironment():
	global sc,sql
	conf = SparkConf()
	#conf.setMaster("spark://192.168.246.236:7077")
	conf.setMaster("local[*]")
	conf.setAppName("Flask")
	conf.set("spark.cassandra.connection.host","192.168.246.236")
	conf.set("spark.executor.memory", "10g")
	conf.set("spark.num.executors","1")
	
	sc = SparkContext(conf=conf)
	#sc = SparkContext("local[*]")
	#sc.setLogLevel("INFO")
	sql = SQLContext(sc)
	spark = SparkSession(sc)

	print ("SparkContext => ",sc)
	print ("SQLContext => ",sql)


def stopEnvironment(context):
	context.stop()



if __name__ == "__main__":
	try:
		sys.path.insert(1, '/home/ubuntu/TFM/dataminingScripts/weather/ml')
		app.run(host= '0.0.0.0')
		if 'sc' in globals():
			sc.stop()
	except:
		print("Oooops, something went wrong when closing the app")
		sc.stop()

