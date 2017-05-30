from pyspark import SparkContext, SparkConf

from pyspark.ml.feature import VectorAssembler, StringIndexer

from pyspark.sql import SQLContext, SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import avg
from pyspark.sql.utils import IllegalArgumentException

from cassandra.cluster import Cluster

from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
from pyspark.ml.classification import NaiveBayes
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
  
from pyspark.mllib.linalg import Vectors


import pyspark
import pandas as pd
import datetime
import time
import numpy as np
import math

def getStationsIds(stations):
	return stations.select("station_id","name","province").collect()

# keep relevant features for now
def extract_features(row,columnName):
	features = [float(row.max_temp)] + [float(row.med_temp)] + [float(row.min_temp)] + [float(row.max_pressure)] +[float(row.min_pressure)] +\
	[float(row.max_pressure)] +[float(row.min_pressure)] +\
	[float(row.precip) if not row.precip is None else 0]+\
	[float(row.insolation) if not row.insolation is None else 0]
	[float(row.wind_med_vel) if not row.wind_med_vel is None else 0] +\
	[float(row.wind_dir) if not row.wind_dir is None else 0] +\
	[float(row.wind_streak) if not row.wind_streak is None else 0]
	return features


def insertDataIntoDatabase(dataToInsert):
	pandas_df = dataToInsert.toPandas()
	for index,row in pandas_df.iterrows():
		station_id = row["station_id"]
		stationIndex = row["stationIndex"]
		prediction = row["prediction"]

		realStationData = indexed[indexed.stationIndex == stationIndex]
		realProvinces = realStationData.select("province")
		predictedProvince = realProvinces.collect()[0][0]

		province = stations[stations.station_id==station_id].select("province").collect()[0][0]
		
		#print("StationId: "+station_id+"\tprovince:" + str(province) +"\tStationIndex:" + str(stationIndex) +"\tPredicted Val: " + str(prediction))
		print("StationId: "+station_id+"\tReal province:" + str(province) +"\tPredicted Province: " + str(predictedProvince) +"\tStationIndex Val:" + str(stationIndex) +"\tPredicted Val: " + str(prediction))
		session.execute("INSERT INTO Station_Naive_Bayes_Prediction (station_id,\"stationIndex\",prediction,province) VALUES (%s, %s, %s, %s)",[str(station_id), stationIndex, prediction,str(province)])



def doBayes(data):
	
	groupedData = data.groupBy("stationIndex","station_id").agg(avg("max_temp"),avg("med_temp"),avg("min_temp"),avg("max_pressure"),avg("min_pressure"),avg("precip"),avg("insolation"))
	selectedData = groupedData.select("station_id","stationIndex","avg(max_temp)","avg(med_temp)","avg(min_temp)","avg(max_pressure)","avg(min_pressure)","avg(precip)","avg(insolation)")
	
	columnsToPredict = ["stationIndex","avg(max_temp)","avg(med_temp)","avg(min_temp)","avg(max_pressure)","avg(min_pressure)","avg(precip)","avg(insolation)"]
	assembler = VectorAssembler(inputCols=columnsToPredict,outputCol="features")
	assembledData = assembler.transform(selectedData)

	#sampledData = assembledData.sample(False,0.1)
	sampledData = assembledData
	
	feature_data = sampledData.withColumn("label",sampledData.stationIndex).withColumn("features",sampledData.features)
	
	print("Sampling...")
	test_data = feature_data.sample(False,0.1)
	train_data = feature_data.sample(False,0.9)
	train_data.cache()
	print("Test data: " + str(test_data.count())+ " , Train data: " + str(train_data.count()))

	nb = NaiveBayes(modelType="multinomial")

	paramGrid = ParamGridBuilder().addGrid(nb.smoothing, [1,2,3,4,5,6,7,8,9,10]).build()

	crossval = CrossValidator(estimator=nb,estimatorParamMaps=paramGrid,evaluator=BinaryClassificationEvaluator())

	print("Training the model...")
	# train the model
	model = crossval.fit(train_data)

	print("Predicting...")
	predictions = model.transform(feature_data)
	#predictions.select("station_id","stationIndex","prediction").show()
	insertDataIntoDatabase(predictions)

	# compute accuracy on the test set
	print("Evaluating...")
	evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction",metricName="accuracy")
	accuracy = evaluator.evaluate(predictions)
	print("Test set accuracy = " + str(accuracy))


if __name__ == "__main__":
	start_time = time.time()

	global stations,dailyData,indexed
	conf = SparkConf()
	conf.setMaster("spark://192.168.246.236:7077")
	conf.setAppName("NaiveBayes Classification Spark2")
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

	##Make a join clean_data with stations in order to get the province
	joinedData = clean_data.join(stations,["station_id"])

	indexer = StringIndexer(inputCol="province", outputCol="stationIndex")
	indexed = indexer.fit(joinedData).transform(joinedData)


	doBayes(indexed)
	
	print("--- %s seconds ---" % (time.time() - start_time))
	print ("END!!!")
	sc.stop()
