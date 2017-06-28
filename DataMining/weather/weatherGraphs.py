import matplotlib
import os
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

matplotlib.use('Agg')

from cassandra.cluster import Cluster
from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext, SparkSession


def initEnvironment():
    global sc, sql, cluster, session

    conf = SparkConf()
    conf.setMaster("spark://192.168.246.236:7077")
    conf.setAppName("Spark Graphs Generation")
    conf.set("spark.cassandra.connection.host", "192.168.246.236")
    conf.set("spark.executor.memory", "10g")
    conf.set("spark.num.executors", "2")

    sc = SparkContext(conf=conf)
    sql = SQLContext(sc)
    cluster = Cluster(['192.168.246.236'])
    session = cluster.connect("dev")


def loadData():
    global stations, clean_daily
    stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")
    clean_daily = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev",
                                                                         table="clean_daily_measurement")


def createDir(dirName):
    if not os.path.exists(dirName):
        os.makedirs(dirName)


def generateGraphs():
    start_time = time.time()

    basePath = "/home/ubuntu/GSOC17/FlOYBD/Flask/graphs/"
    stationsPd = stations.toPandas()
    columnsList = ["max_temp", "med_temp", "min_temp", "max_pressure", "min_pressure", "precip", "insolation"]
    stationCount = 1
    for index, row in stationsPd.iterrows():
        print(str(stationCount) + ":\t" + row.station_id)
        stationpath = basePath + row.station_id
        createDir(stationpath)
        station_data = clean_daily[clean_daily.station_id == row.station_id]
        dataframe = station_data.toPandas()
        for column in columnsList:
            dataframe[column] = dataframe[column].apply(pd.to_numeric)
            plot = dataframe.plot(y=column, x='measure_date', figsize=(20, 15), marker='o')
            fig = plot.get_figure()
            fig.savefig(stationpath + "/" + row.station_id + "_" + column + ".png")
            plt.close(fig)
        stationCount += 1
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    # matplotlib.style.use('ggplot')

    initEnvironment()
    loadData()
    generateGraphs()
