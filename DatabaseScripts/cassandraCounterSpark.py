
import pyspark
import os.path
import time
from pyspark import SparkContext,SparkConf

from pyspark.sql import SQLContext
from pyspark.sql.functions import count
from collections import defaultdict


def initEnvironment():
	global sc,sql
	conf = SparkConf()
	spark_home = os.environ.get('SPARK_HOME', None)
	conf.setMaster("spark://192.168.246.236:7077")
	conf.setAppName("Database Counter")
	conf.set("spark.cassandra.connection.host","192.168.246.236")
	conf.set("spark.executor.memory", "10g")
	#conf.set("spark.num.executors","2")

	sc = SparkContext(conf=conf)
	#sc = pyspark.SparkContext('local[*]')
	sql = SQLContext(sc)


def loadData():
	global stations,monthly,daily,earthquakes,station_limits,clean_daily,regression,bayes
	stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")
	station_limits = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station_limits")
	monthly = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="monthly_measurement")
	daily = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="daily_measurement")
	earthquakes = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="earthquake")
	clean_daily = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="clean_daily_measurement")
	regression = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station_regression_prediction")
	bayes = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station_naive_bayes_prediction")


def printValues():
	#print("SparkContext => ", sc)
	#print("SQLContext => ", sql)
	print("Monthly Measurements:", monthly.count())
	print("Daily Measurements:", daily.count())
	print("Clean Daily Measurements:", clean_daily.count())
	print("Stations:", stations.count())
	print("Stations Limits:", station_limits.count())
	print("Linear Regression:", regression.count())
	print("Naive-Bayes Classification:", bayes.count())
	print("Earthquakes:", earthquakes.count())

if __name__ == "__main__":
	start_time = time.time()
	initEnvironment()
	loadData()
	printValues()
	print("--- %s seconds ---" % (time.time() - start_time))
	print("END")
