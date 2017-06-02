from datetime import datetime

from cassandra.cluster import Cluster
from cassandra.query import named_tuple_factory

from pyspark import SparkContext,SparkConf
from pyspark.ml.regression import LinearRegression,LinearRegressionModel
from pyspark.ml.tuning import TrainValidationSplitModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import max,min,col,avg,count
from pyspark.sql.types import *

from utils import generalFunctions

import os
import time
import pickle
import json
import pyspark

def getConcreteWeatherData(daily_measures,station_id,date,allStations):
	datetime_object = datetime.strptime(date, '%Y-%m-%d').date()

	if str(allStations)==str("True"):
		print("All Stations")
		measurement = daily_measures.filter((daily_measures.measure_date==datetime_object))
	else:	
		print("One Station")
		measurement = daily_measures.filter((daily_measures.measure_date==datetime_object) & (daily_measures.station_id == station_id))

	return measurement

def getConcreteEarhquakesData(earthquakes,date,max_lat,min_lat,max_lon,min_lon):
	start_time = time.time()
	

	datetime_object = datetime.strptime(date, '%Y-%m-%d').date()
	datetimeStr = datetime_object.strftime("%Y-%m-%d")

	#cluster = Cluster(['192.168.246.236'])
	#session = cluster.connect("dev")
	#session.row_factory = named_tuple_factory

	#queryStr = 'SELECT place,latitude,longitude,magnitude,geojson,fecha FROM earthquake WHERE fecha<=\''+datetimeStr+'\' AND longitude < '+max_lon+' AND longitude >'+min_lon +' AND latitude < '+max_lat+' AND latitude >'+min_lat+' ALLOW FILTERING'

	#rows = session.execute(queryStr)
	#data = []
	#for row in rows:
	#	earthquake = {}
	#	earthquake["place"] = row.place
	#	earthquake["latitude"] = float(row.latitude) if row.latitude is not None else 0
	#	earthquake["longitude"] = float(row.longitude) if row.longitude is not None else 0
	#	earthquake["magnitude"] = float(row.magnitude) if row.magnitude is not None else 0
	#	earthquake["geojson"] = row.geojson
	#	earthquake["fecha"] = row.fecha
	#	data.append(earthquake)

	earthquakesResult = earthquakes.filter((earthquakes.fecha >= datetime_object)
		& (earthquakes.longitude <= max_lon) & (earthquakes.longitude >= min_lon) 
		& (earthquakes.latitude <= max_lat) & (earthquakes.latitude >= min_lat))

	print("--- %s seconds ---" % (time.time() - start_time))
	return earthquakesResult


def getStationInfo(stations,station_id):
	stationData = stations.filter(stations.station_id == station_id)
	return stationData

def loadModelFromDatabase(columnName,station_id):
	cluster = Cluster(['192.168.246.236'])
	session = cluster.connect("dev")
	name = str(station_id+"__"+columnName)
	query = "SELECT model FROM linear_model WHERE name=%s"
	rows = session.execute(query, parameters=[(name)])
	#rows = session.execute('SELECT model FROM linear_model WHERE name=\"'+name+'\"')
	if(rows):
		for row in rows:
			loadedCustomModel = pickle.loads(row[0])
			loadedModel = loadedCustomModel.getModel()
	
			lrModel = TrainValidationSplitModel(loadedModel)
			return row[0]


def predict(sql,sc,columns,station_id,currentWeather):
	columnsToPredict = ["max_temp","med_temp","min_temp","max_pressure","min_pressure","precip","insolation"]
	returnedPredictions = []
	
	#schema = StructType([])

	field = [StructField("station_id",StringType(), True),
	StructField("max_temp", FloatType(), True),\
	 StructField("max_temp", FloatType(), True),\
	 StructField("med_temp", FloatType(), True),\
	 StructField("min_temp", FloatType(), True),\
	 StructField("max_pressure", FloatType(), True),\
	 StructField("min_pressure", FloatType(), True),\
	 StructField("precip", FloatType(), True),\
	 StructField("insolation", FloatType(), True),\
	 StructField("prediction_max_temp", FloatType(), True),\
	 StructField("prediction_max_temp", FloatType(), True),\
	 StructField("prediction_med_temp", FloatType(), True),\
	 StructField("prediction_min_temp", FloatType(), True),\
	 StructField("prediction_max_pressure", FloatType(), True),\
	 StructField("prediction_min_pressure", FloatType(), True),\
	 StructField("prediction_precip", FloatType(), True),\
	 StructField("prediction_insolation", FloatType(), True)]

	schema = StructType(field)

	resultDataframe = sql.createDataFrame(sc.emptyRDD(), schema)


	fields1 = [StructField("station_id",StringType(), True),
	StructField("max_temp", FloatType(), True),\
	 StructField("med_temp", FloatType(), True),\
	 StructField("min_temp", FloatType(), True),\
	 StructField("max_pressure", FloatType(), True),\
	 StructField("min_pressure", FloatType(), True),\
	 StructField("precip", FloatType(), True),\
	 StructField("insolation", FloatType(), True)]

	schema1 = StructType(fields1)

	resultDataframe = sql.createDataFrame(sc.emptyRDD(), schema)
	firstTime = True

	for column in columns:
		modelPath = "models/"+station_id+"__"+column
		if not os.path.exists(modelPath):
			print("####No Model")
			break

		lrModel = LinearRegressionModel.load(modelPath)

		assembler = VectorAssembler(inputCols=[column],outputCol="features")
				
		df_for_predict = sql.createDataFrame([(currentWeather["station_id"],
		 float(currentWeather["max_temp"]),# if column != "max_temp" else None,
		 float(currentWeather["med_temp"]),#  if column != "med_temp" else None,
		 float(currentWeather["min_temp"]),#  if column != "min_temp" else None,
		 float(currentWeather["max_pres"]),#  if column != "max_pres" else None,
		 float(currentWeather["min_pres"]),#  if column != "min_pres" else None,
		 float(currentWeather["precip"]),#  if column != "precip" else None,
		 float(currentWeather["insolation"]),# if column != "insolation" else None,
		 )],schema1)

		
		assembledTestData = assembler.transform(df_for_predict)
		prediction_data = assembledTestData.withColumn("label",df_for_predict[column]).withColumn("features",assembledTestData.features)

		predictions = lrModel.transform(prediction_data).select("station_id",column,"prediction")
		#predictions.show()

		#predictions = lrModel.evaluate(prediction_data)
		#print(predictions.predictions.show())

		predictions1 = predictions.withColumn(str("prediction_"+column),predictions.prediction)
		#predictions = lrModel.transform(prediction_data)

		
		returnedPredictions.append(generalFunctions.dataframeToJson(predictions1))

	#resultDataframe = sql.createDataFrame(returnedPredictions)
	return json.dumps(returnedPredictions)


def getLimitsForStation(stations_limits,station_id):
	return stations_limits.filter(stations_limits.station_id == station_id)


def getLimitsAllStationsWithInterval(clean_daily,dateFrom,dateTo):

	datetime_object_from = datetime.strptime(dateFrom, '%Y-%m-%d').date()
	datetime_object_to = datetime.strptime(dateTo, '%Y-%m-%d').date()

	tmpDf = clean_daily.filter((clean_daily.measure_date>=datetime_object_from) & (clean_daily.measure_date<=datetime_object_to))
	groupedDf = tmpDf.groupBy("station_id").agg(avg("max_temp"),avg("med_temp"),avg("min_temp"),
		avg("max_pressure"),avg("min_pressure"),
		avg("precip"),avg("insolation"))

	groupedDf.show()

	return groupedDf.select("station_id","avg(max_temp)","avg(med_temp)","avg(min_temp)",
		"avg(max_pressure)","avg(min_pressure)","avg(precip)","avg(insolation)")

def getLimitsStationWithInterval(clean_daily,station_id,dateFrom,dateTo):

	datetime_object_from = datetime.strptime(dateFrom, '%Y-%m-%d').date()
	datetime_object_to = datetime.strptime(dateTo, '%Y-%m-%d').date()

	tmpDf = clean_daily.filter((clean_daily.measure_date>=datetime_object_from) & (clean_daily.measure_date<=datetime_object_to) &
		(clean_daily.station_id==station_id))
	groupedDf = tmpDf.groupBy("station_id").agg(avg("max_temp"),avg("med_temp"),avg("min_temp"),
		avg("max_pressure"),avg("min_pressure"),
		avg("precip"),avg("insolation"))

	groupedDf.show()

	return groupedDf.select("station_id","avg(max_temp)","avg(med_temp)","avg(min_temp)",
		"avg(max_pressure)","avg(min_pressure)","avg(precip)","avg(insolation)")