from pyspark import SparkContext,SparkConf
import pyspark
from pyspark.sql import SQLContext
from pyspark.sql.functions import max,col, avg,sum

from cassandra.cluster import Cluster

import os.path
import json
import numpy as np

from collections import defaultdict
import pandas as pd


def getStationsIds(stations):
	return stations.select("station_id","name").collect()

def fillNullTempValues(station_data):

	averages = station_data.agg(
		avg(col("max_temp")),
		avg(col("med_temp")),
		avg(col("min_temp")),
		avg(col("max_pressure")),
		avg(col("min_pressure")),
		avg(col("precip")),
		avg(col("insolation")))
	averageMaxTemp = averages.select("avg(max_temp)").collect()[0]
	averageMinTemp = averages.select("avg(min_temp)").collect()[0]
	averageMedTemp = averages.select("avg(med_temp)").collect()[0]
	averageMaxPressure = averages.select("avg(max_pressure)").collect()[0]
	averageMinPressure = averages.select("avg(min_pressure)").collect()[0]
	averagePrecip = averages.select("avg(precip)").collect()[0]
	averageInsolation = averages.select("avg(insolation)").collect()[0]

	cleanedStationData = station_data.select(
		"station_id",
		"measure_date",
		"max_temp_hour",
		"min_temp_hour",
		"max_temp",
		"min_temp",
		"med_temp",
		"max_press_hour",
		"min_press_hour",
		"max_pressure",
		"min_pressure",
		"precip",
		"wind_med_vel",
		"wind_dir",
		"wind_streak",
		"wind_streak_hour",
		"insolation").fillna(
		{"max_temp":float(averageMaxTemp[0]),
		"min_temp":float(averageMinTemp[0]),
		"med_temp":float(averageMedTemp[0]),
		"max_pressure":float(averageMaxPressure[0]) if not averageMaxPressure[0] is None else 0,
		"min_pressure":float(averageMinPressure[0]) if not averageMinPressure[0] is None else 0,
		"precip":float(averagePrecip[0]) if not averagePrecip[0] is None else 0,
		"wind_dir":float(0),
		"wind_med_vel":float(0),
		"insolation":float(averageInsolation[0]) if not averageInsolation[0] is None else 0
		})

	return cleanedStationData

def fillEmptyValues(station_data):
	stationData = fillNullTempValues(station_data)
	return stationData

def insertCleanedData(data):
	"""
	Insert one row into daily_measurement table
	"""
	tMax = float(str(data['max_temp']).replace(",",".")) if not (data['max_temp'] is None) else None
	tMed = float(str(data['med_temp']).replace(",",".")) if not (data['med_temp'] is None) else None
	tMin = float(str(data['min_temp']).replace(",",".")) if not (data['min_temp'] is None) else None
	presMax = float(str(data['max_pressure']).replace(",",".")) if not (data['max_pressure'] is None) else None
	presMin = float(str(data['min_pressure']).replace(",",".")) if not (data['min_pressure'] is None) else None
	try:
		prec = float(str(data['precip']).replace(",",".")) if not (data['precip'] is None) else None
	except (ValueError):
		prec = None
	velmedia = float(str(data['wind_med_vel']).replace(",",".")) if not (data['wind_med_vel'] is None) else None
	racha = float(str(data['wind_streak']).replace(",",".")) if not (data['wind_streak'] is None) else None
	sol = float(str(data['insolation']).replace(",",".")) if not (data['insolation'] is None) else None

	session.execute("INSERT INTO Clean_Daily_Measurement (station_id,measure_date,max_temp_hour,min_temp_hour,max_temp,\
					med_temp,min_temp,max_press_hour,min_press_hour,max_pressure,min_pressure,precip,wind_med_vel,wind_dir,\
					wind_streak,wind_streak_hour,insolation) \
					VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
					,[str(data["station_id"]), data['measure_date'], data['max_temp_hour'], data['min_temp_hour'],
					tMax, tMed, tMin, data['max_press_hour'], data['min_press_hour'], presMax, presMin,
					prec, velmedia, data['wind_dir'], racha, data['wind_streak_hour'], sol])


if __name__ == "__main__":
	global stations,dailyData
	conf = SparkConf()
	conf.setMaster("spark://192.168.246.236:7077")
	#conf.setMaster("local[2]")
	conf.setAppName("Spark Cleaner")
	conf.set("spark.cassandra.connection.host","192.168.246.236")
	conf.set("spark.executor.memory", "10g")
	conf.set("spark.num.executors","2")
	
	cluster = Cluster(['192.168.246.236'])
	session = cluster.connect("dev")

	sc = SparkContext(conf=conf)
	sql = SQLContext(sc)

	print ("SparkContext => ",sc)
	print ("SQLContext => ",sql)

	stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")
	dailyData = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="daily_measurement")

	stationsIds = getStationsIds(stations)
	stationCount = 1
	for station in stationsIds:
			#print("Processing station"+str(stationCount) + " : " + str(station.station_id)+"-"+str(station.name))
			print("Processing station"+str(stationCount))
			station_data = dailyData[dailyData.station_id==station.station_id]
			cleanedStationData = fillEmptyValues(station_data)
			
			pandas_df = cleanedStationData.toPandas()
			for index, row in pandas_df.iterrows():
				insertCleanedData(row)
			stationCount += 1
			

	print ("END!!!")
