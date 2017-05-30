from pyspark import SparkContext, SparkConf

from pyspark.ml.feature import VectorAssembler, StringIndexer

from pyspark.sql import SQLContext, SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import avg
from pyspark.sql.utils import IllegalArgumentException

from cassandra.cluster import Cluster

from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
from pyspark.ml.clustering import KMeans

from pyspark.mllib.linalg import Vectors


import pyspark
import pandas as pd
import datetime
import time
import numpy as np
import math


def getStationsIds(stations):
	return stations.select("station_id","name").collect()

# keep relevant features for now
def extract_features(row,columnName):
	features = [float(row.max_temp)] + [float(row.med_temp)] + [float(row.min_temp)] + [float(row.max_pressure)] +[float(row.min_pressure)] +\
	[float(row.max_pressure)] +[float(row.min_pressure)] +\
	[float(row.precip) if not row.precip is None else 0]+\
	[float(row.insolation) if not row.insolation is None else 0]
	#[float(row.wind_med_vel) if not row.wind_med_vel is None else 0] +\
	#[float(row.wind_dir) if not row.wind_dir is None else 0] +\
	#[float(row.wind_streak) if not row.wind_streak is None else 0] +\
	#print (features)
	return features

def insertDataIntoDatabase(dataToInsert):
	station_id = dataToInsert.select("station_id").collect()[0][0]
	stationIndex = dataToInsert.select("stationIndex").collect()[0][0]
	prediction = dataToInsert.select("prediction").collect()[0][0]
	print("Station: " + str(station_id)+"\tReal Val:" + str(stationIndex) +"\tPredicted Val: " + str(prediction))
	session.execute("INSERT INTO Station_NaiveBayes_Prediction (station_id,station_index,prediction)\
		VALUES (%s, %s, %s)",[str(station_id), station_index, predictedVal])


def doKMeans(data):
	
	#groupedData = data.groupBy("station_id","stationIndex").agg(avg("max_temp"),avg("med_temp"),avg("min_temp"),avg("max_pressure"),avg("min_pressure"),avg("precip"),avg("insolation"))
	#selectedData = groupedData.select("station_id","stationIndex","avg(max_temp)","avg(med_temp)","avg(min_temp)","avg(max_pressure)","avg(min_pressure)","avg(precip)","avg(insolation)")
	
	#columnsToPredict = ["stationIndex","avg(max_temp)","avg(med_temp)","avg(min_temp)","avg(max_pressure)","avg(min_pressure)","avg(precip)","avg(insolation)"]
	#assembler = VectorAssembler(inputCols=columnsToPredict,outputCol="features")
	#assembledData = assembler.transform(selectedData)

	#groupedData = data.groupBy("station_id","stationIndex").agg(avg("max_temp"),avg("med_temp"),avg("min_temp"),avg("max_pressure"),avg("min_pressure"),avg("precip"),avg("insolation"))
	#selectedData = groupedData.select("station_id","stationIndex","avg(max_temp)","avg(med_temp)","avg(min_temp)","avg(max_pressure)","avg(min_pressure)","avg(precip)","avg(insolation)")
	
	columnsToPredict = ["stationIndex","max_temp","med_temp","min_temp","max_pressure","min_pressure","precip","insolation"]
	assembler = VectorAssembler(inputCols=columnsToPredict,outputCol="features")
	assembledData = assembler.transform(data)

	sampledData = assembledData
	
	feature_data = sampledData.withColumn("label",sampledData.stationIndex).withColumn("features",sampledData.features)
	

	print("Sampling...")
	test_data = feature_data.sample(False,0.1)
	train_data = feature_data.sample(False,0.9)
	print("Test data: " + str(test_data.count())+ " , Train data: " + str(train_data.count()))
	

	# Trains a k-means model.
	#kmeans = KMeans().setK(stations.count()).setSeed(1)
	kmeans = KMeans().setK(stations.count()).setSeed(1)
	model = kmeans.fit(feature_data)

	# Evaluate clustering by computing Within Set Sum of Squared Errors.
	wssse = model.computeCost(feature_data)
	print("Within Set Sum of Squared Errors = " + str(wssse))

	# Shows the result.
	centers = model.clusterCenters()
	print("Cluster Centers: ")
	for center in centers:
		print(center)

	print("Predicting...")
	predictions = model.transform(test_data)
	#predictions.show()
	predictions.select("station_id","stationIndex","label","prediction").show()

if __name__ == "__main__":
	start_time = time.time()

	global stations,dailyData
	conf = SparkConf()
	conf.setMaster("spark://192.168.246.236:7077")
	conf.setAppName("KMeans Clustering Spark2")
	conf.set("spark.cassandra.connection.host","192.168.246.236")
	conf.set("spark.executor.memory", "10g")
	conf.set("spark.num.executors","2")

	cluster = Cluster(['192.168.246.236'])
	session = cluster.connect("dev")
		
	sc = SparkContext(conf=conf)
	sql = SQLContext(sc)
	spark = SparkSession(sc)

	print ("SparkContext => ",sc)
	print ("SQLContext => ",sql)

	stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")
	clean_data = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="clean_daily_measurement")

	stationsIds = getStationsIds(stations)
	stationCount = 1

	indexer = StringIndexer(inputCol="station_id", outputCol="stationIndex")
	indexed = indexer.fit(clean_data).transform(clean_data)

	doKMeans(indexed)

	
	print("--- %s seconds ---" % (time.time() - start_time))
	print ("END!!!")
	sc.stop()
