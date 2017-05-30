from pyspark import SparkContext, SparkConf

from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.regression import LinearRegression
from pyspark.ml.tuning import ParamGridBuilder, TrainValidationSplit
from pyspark.ml.feature import VectorAssembler

from pyspark.sql import SQLContext, SparkSession
from pyspark.sql import Row
from pyspark.sql.functions import avg
from pyspark.sql.types import *
from pyspark.sql.utils import IllegalArgumentException
from pyspark.sql.functions import UserDefinedFunction

from cassandra.cluster import Cluster

import pyspark
import pandas as pd
import datetime
import time
import numpy as np
import math
import os, uuid
import pickle
import shutil
import py4j


from CustomModel import CustomModel

def clearColumn(dataframe, columnName):
	udf = UserDefinedFunction(lambda x: float(0), FloatType())
	new_df = dataframe.select(*[udf(column).alias(columnName) if column == columnName else column for column in dataframe.columns])
	return new_df

def assignValue(dataframe, columnName, value):
	udf = UserDefinedFunction(lambda x: value, FloatType())
	new_df = dataframe.select(*[udf(column).alias(columnName) if column == columnName else column for column in dataframe.columns])
	return new_df

def getStationsIds(stations):
	return stations.select("station_id","name").collect()


def insertDataIntoDatabase(dataToInsert,columnName,station_id):
	realValStr = dataToInsert.select("avg("+columnName+")").collect()[0][0]
	realVal = float(realValStr)
	predictedValStr = dataToInsert.select("avg(prediction)").collect()[0][0]
	predictedVal = float(predictedValStr)
	print("Real Val:" + str(realVal) +"\tPredicted Val: " + str(predictedVal)+"\t Prediction Diff: " + str(realVal-predictedVal))
	session.execute("INSERT INTO Station_Regression_Prediction (station_id,"+columnName+","+columnName+"_pred"")\
		VALUES (%s, %s, %s)",[str(station_id), realVal, predictedVal])

def parseFunction(row):
	print (row)

def saveModelToDatabase(model,station_id,columnName):
	name = str(station_id+"__"+columnName)
	print("Saving the model..."+str(name))
	#fid = uuid.uuid4()
	#res = bytearray([model])
	res = pickle.dumps(CustomModel(model),fix_imports=False)
	session.execute("INSERT INTO linear_model (name,model) VALUES (%s, %s)", (name, res))



def saveModel(model,station_id,columnName):
	directory = "/home/ubuntu/TFM/flask/models"
	if not os.path.exists(directory):
	    os.makedirs(directory)

	path = directory+"/"+station_id+"__"+columnName
	print("Saving the model in..."+str(path))
	
	model.save(str(path))


def predictDataForStation(stationData,columnName,station_id):


	columnsList = ["max_temp","med_temp","min_temp","max_pressure","min_pressure","precip","insolation"]
	#assembler = VectorAssembler(inputCols=columnsList,outputCol="features")
	assembler = VectorAssembler(inputCols=[columnName],outputCol="features")
	assembledData = assembler.transform(stationData)

	feature_data = assembledData.withColumn("label",stationData[columnName]).withColumn("features",assembledData.features)
	
	print("Getting training data...")
	test_data = feature_data.sample(False,0.1)
	train_data = feature_data.sample(False,0.9)
	print("Test data: " + str(test_data.count())+ " , Train data: " + str(train_data.count()))

	#BestModel
	#lr = LinearRegression(maxIter=10)
	lr = LinearRegression()
	#lr.setSolver("l-bfgs")

	paramGrid = ParamGridBuilder()\
	.addGrid(lr.regParam, [0.1,0.01,0.001,0.0001,0.0001]) \
	.addGrid(lr.fitIntercept, [False, True]) \
	.addGrid(lr.maxIter, [1,10,50,100]) \
	.build()

	try:
		print("Calculating and training the best model")
		tvs = TrainValidationSplit(estimator=lr, estimatorParamMaps=paramGrid,evaluator=RegressionEvaluator(),trainRatio=0.8)
		# Fit the model
		lrModel = tvs.fit(train_data)
		#saveModelToDatabase(lrModel.bestModel,station_id,columnName)
		#saveModel(lrModel.bestModel,station_id,columnName)

		
		##### AQUESTES LINIES SON LES BONES!!!!######
		predictions = lrModel.transform(test_data).select("measure_date","station_id",columnName,"prediction")
		groupedPredictions = predictions.groupBy("station_id").agg(avg(columnName),avg("prediction"))
		insertDataIntoDatabase(groupedPredictions,columnName,station_id)

		
		#Amb valors nous, es prediu la nova columna. Es podria fer que amb valors de pressio, predis les temperatures		
		#df_for_predict = sql.createDataFrame([(station_id,0,5,0,950,900,0,0)], ["station_id","max_temp","med_temp","min_temp","max_pressure","min_pressure","precip","insolation"])	
		#assembledTestData = assembler.transform(df_for_predict)
		#predictions = lrModel.transform(assembledTestData).select("station_id",columnName,"prediction")
		#predictions.show()

	except IllegalArgumentException as error:
		print("#####IllegalArgumentException on :\t " +str(station_id)+" on "+str(columnName)+"#####")
		print("IllegalArgumentException : {0}".format(error))
	except py4j.protocol.Py4JJavaError as error:
		print("#####Py4JJavaError on :\t " +str(station_id)+" on "+str(columnName)+"#####")
		print("Py4JJavaError : {0}".format(error))

if __name__ == "__main__":
	start_time = time.time()

	global stations,dailyData,sc
	conf = SparkConf()
	#conf.setMaster("spark://192.168.246.236:7077")
	conf.setMaster("local[*]")
	conf.setAppName("Linear Regression Spark2")
	conf.set("spark.cassandra.connection.host","192.168.246.236")
	conf.set("spark.executor.memory", "10g")
	conf.set("spark.num.executors","2")

	cluster = Cluster(['192.168.246.236'])
	session = cluster.connect("dev")
		
	sc = SparkContext(conf=conf)
	#sc.setLogLevel("INFO")
	sql = SQLContext(sc)
	spark = SparkSession(sc)

	print ("SparkContext => ",sc)
	print ("SQLContext => ",sql)

	#shutil.rmtree('/home/ubuntu/TFM/flask/models')
	
	stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")
	clean_data = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="clean_daily_measurement")

	stationsIds = getStationsIds(stations)
	stationCount = 1

	columnsToPredict = ["max_temp","med_temp","min_temp","max_pressure","min_pressure","precip","insolation"]

	for station in stationsIds:
		print("##############\tProcessing station #"+str(stationCount)+" :\t " + str(station.station_id)+"-"+str(station.name.encode('utf-8'))+"\t##############")
		data = clean_data[clean_data.station_id == station.station_id]
		for column in columnsToPredict:
			print("Processing column "+column)
			predictDataForStation(data,column,station.station_id)
		stationCount += 1

	
	print("--- %s seconds ---" % (time.time() - start_time))
	print ("END!!!")
	sc.stop()
