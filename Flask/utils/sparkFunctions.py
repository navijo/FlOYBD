from datetime import datetime
from cassandra.cluster import Cluster
import pyspark
from pyspark import SparkContext,SparkConf

from pyspark.sql.functions import col
from pyspark.ml.regression import LinearRegression,LinearRegressionModel
import os
import time
import pickle
from pyspark.ml.tuning import TrainValidationSplitModel
from pyspark.ml.feature import VectorAssembler

from pyspark.sql.types import *
from cassandra.query import named_tuple_factory
from utils import generalFunctions

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

	firstTime = True

	for column in columns:
		modelPath = "models/"+station_id+"__"+column
		if not os.path.exists(modelPath):
			print("####No Model")
			break

		assembler = VectorAssembler(inputCols=[column],outputCol="features")
				
		lrModel = LinearRegressionModel.load(modelPath)
	
		df_for_predict = sql.createDataFrame([(currentWeather["station_id"],
		 float(currentWeather["max_temp"]), float(currentWeather["med_temp"]),float(currentWeather["min_temp"]),
			 float(currentWeather["max_pres"]),float(currentWeather["min_pres"]),
			 float(currentWeather["precip"]),float(currentWeather["insolation"]))],
		 ["station_id","max_temp","med_temp","min_temp","max_pressure","min_pressure","precip","insolation"])

		assembledTestData = assembler.transform(df_for_predict)
		prediction_data = assembledTestData.withColumn("label",df_for_predict[column]).withColumn("features",assembledTestData.features)

		predictions = lrModel.transform(prediction_data).select("station_id",column,"prediction")
		predictions1 = predictions.withColumn(str("prediction_"+column),predictions.prediction)
		#predictions = lrModel.transform(prediction_data)

		
		returnedPredictions.append(generalFunctions.dataframeToJson(predictions1))

	#resultDataframe = sql.createDataFrame(returnedPredictions)
	return returnedPredictions