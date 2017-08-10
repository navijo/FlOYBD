import pyspark
import os.path
import numpy as np
import pandas as pd
import time
import json

from cylinders import CylindersKml
from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext
from pyspark.sql.functions import max, min, col, avg, count
from collections import defaultdict
from cassandra.cluster import Cluster
from datetime import datetime


def initEnvironment():
    global sc, sql, cluster, session

    conf = SparkConf()
    conf.setMaster("spark://192.168.246.236:7077")
    conf.setAppName("Spark Weather Functions")
    conf.set("spark.cassandra.connection.host", "192.168.246.236")
    conf.set("spark.executor.memory", "10g")
    conf.set("spark.num.executors", "2")

    spark_home = os.environ.get('SPARK_HOME', None)
    sc = SparkContext(conf=conf)
    sql = SQLContext(sc)
    cluster = Cluster(['192.168.246.236'])
    session = cluster.connect("dev")


def loadData():
    global stations, monthly, daily
    stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")
    monthly = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="monthly_measurement")
    daily = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="clean_daily_measurement")


def getStationValueDate(pStationId, date):
    startDate = datetime.strptime(date, '%Y-%M-%d')
    stationData = daily[(daily.station_id == pStationId) & (daily.measure_date == date)]
    jsonData = dataframeToJson(stationData)
    if len(json.loads(jsonData)['measure_date']) > 0:
        return jsonData
    else:
        return ""


def getMaxValues(pStationId):
    stationMaxs = daily[daily.station_id == pStationId].groupBy('station_id').agg(max('max_temp'), max('max_pressure'),
                                                                                  max('med_temp'), max('min_temp'),
                                                                                  max('precip'), max('wind_med_vel'),
                                                                                  max('wind_streak'))
    returnValue = stationMaxs.join(stations, on=['station_id'], how='left_outer')
    return returnValue


def getMinValues(pStationId):
    stationMins = daily[daily.station_id == pStationId].groupBy('station_id').agg(min('max_temp'), min('max_pressure'),
                                                                                  min('med_temp'), min('min_temp'),
                                                                                  min('precip'), min('wind_med_vel'),
                                                                                  min('wind_streak'))
    returnValue = stationMins.join(stations, on=['station_id'], how='left_outer')
    return returnValue


def getAvgValues(pStationId):
    stationAvgs = daily[daily.station_id == pStationId].groupBy('station_id').agg(avg('max_temp'), avg('max_pressure'),
                                                                                  avg('med_temp'), avg('min_temp'),
                                                                                  avg('precip'), avg('wind_med_vel'),
                                                                                  avg('wind_streak'))
    returnValue = stationAvgs.join(stations, on=['station_id'], how='left_outer')
    return returnValue


def dataframeToJson(dataFrame):
    pandas_df = dataFrame.toPandas()
    return pandas_df.to_json()


def getAndInsertStationLimits(pStationId):
    stationLimits = daily[daily.station_id == pStationId].groupBy('station_id').agg(
        max('max_temp'), avg('max_temp'), min('max_temp'),
        max('max_pressure'), avg('max_pressure'), min('max_pressure'),
        max('min_pressure'), avg('min_pressure'), min('min_pressure'),
        max('med_temp'), avg('med_temp'), min('med_temp'),
        max('min_temp'), avg('min_temp'), min('min_temp'),
        max('precip'), avg('precip'), min('precip'),
        max('wind_med_vel'), avg('wind_med_vel'), min('wind_med_vel'),
        max('wind_streak'), avg('wind_streak'), min('wind_streak'))

    stationLimitsRenamed = stationLimits.select("max(max_temp)", "avg(max_temp)", "min(max_temp)", "max(max_pressure)",
                                                "avg(max_pressure)"
                                                , "min(max_pressure)", "max(med_temp)", "avg(med_temp)",
                                                "min(med_temp)", "max(min_temp)", "avg(min_temp)", "min(min_temp)",
                                                "max(precip)", "avg(precip)", "min(precip)", "max(wind_med_vel)",
                                                "avg(wind_med_vel)", "min(wind_med_vel)", "max(wind_streak)",
                                                "avg(wind_streak)", "min(wind_streak)", "max(min_pressure)",
                                                "avg(min_pressure)", "min(min_pressure)").withColumnRenamed(
        "max(max_temp)", "value1").withColumnRenamed(
        "avg(max_temp)", "value2").withColumnRenamed(
        "min(max_temp)", "value3").withColumnRenamed(
        "max(max_pressure)", "value4").withColumnRenamed(
        "avg(max_pressure)", "value5").withColumnRenamed(
        "min(max_pressure)", "value6").withColumnRenamed(
        "max(med_temp)", "value7").withColumnRenamed(
        "avg(med_temp)", "value8").withColumnRenamed(
        "min(med_temp)", "value9").withColumnRenamed(
        "max(min_temp)", "value10").withColumnRenamed(
        "avg(min_temp)", "value11").withColumnRenamed(
        "min(min_temp)", "value12").withColumnRenamed(
        "max(precip)", "value13").withColumnRenamed(
        "avg(precip)", "value14").withColumnRenamed(
        "min(precip)", "value15").withColumnRenamed(
        "max(wind_med_vel)", "value16").withColumnRenamed(
        "avg(wind_med_vel)", "value17").withColumnRenamed(
        "min(wind_med_vel)", "value18").withColumnRenamed(
        "max(wind_streak)", "value19").withColumnRenamed(
        "avg(wind_streak)", "value20").withColumnRenamed(
        "min(wind_streak)", "value21").withColumnRenamed(
        "max(min_pressure)", "value22").withColumnRenamed(
        "avg(min_pressure)", "value23").withColumnRenamed(
        "min(min_pressure)", "value24").collect()

    maxMaxTemp = stationLimitsRenamed[0].value1
    avgMaxTemp = stationLimitsRenamed[0].value2
    minMaxTemp = stationLimitsRenamed[0].value3
    maxMaxPressure = stationLimitsRenamed[0].value4
    avgMaxPressure = stationLimitsRenamed[0].value5
    minMaxPressure = stationLimitsRenamed[0].value6
    maxMedTemp = stationLimitsRenamed[0].value7
    avgMedTemp = stationLimitsRenamed[0].value8
    minMedTemp = stationLimitsRenamed[0].value9
    maxMinTemp = stationLimitsRenamed[0].value10
    avgMinTemp = stationLimitsRenamed[0].value11
    minMinTemp = stationLimitsRenamed[0].value12
    maxPrecip = stationLimitsRenamed[0].value13
    avgPrecip = stationLimitsRenamed[0].value14
    minPrecip = stationLimitsRenamed[0].value15
    maxWindMedVel = stationLimitsRenamed[0].value16
    avgWindMedVel = stationLimitsRenamed[0].value17
    minWindMedVel = stationLimitsRenamed[0].value18
    maxWindStreak = stationLimitsRenamed[0].value19
    avgWindStreak = stationLimitsRenamed[0].value20
    minWindStreak = stationLimitsRenamed[0].value21
    maxMinPressure = stationLimitsRenamed[0].value22
    avgMinPressure = stationLimitsRenamed[0].value23
    minMinPressure = stationLimitsRenamed[0].value24

    session.execute("INSERT INTO Station_limits (station_id,\"maxMaxTemp\",\"avgMaxTemp\",\"minMaxTemp\",\"maxMaxPressure\",\
        \"avgMaxPressure\",\"minMaxPressure\",\"maxMedTemp\",\"avgMedTemp\",\"minMedTemp\",\"maxMinTemp\",\"avgMinTemp\",\"minMinTemp\",\"maxPrecip\",\
        \"avgPrecip\",\"minPrecip\",\"maxWindMedVel\",\"avgWindMedVel\",\"minWindMedVel\",\"maxWindStreak\",\"avgWindStreak\",\"minWindStreak\",\"maxMinPressure\",\"avgMinPressure\",\"minMinPressure\") \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    , [str(pStationId), maxMaxTemp, avgMaxTemp, minMaxTemp,
                       maxMaxPressure, avgMaxPressure, minMaxPressure,
                       maxMedTemp, avgMedTemp, minMedTemp,
                       maxMinTemp, avgMinTemp, minMinTemp,
                       maxPrecip, avgPrecip, minPrecip,
                       maxWindMedVel, avgWindMedVel, minWindMedVel,
                       maxWindStreak, avgWindStreak, minWindStreak,
                       maxMinPressure, avgMinPressure, minMinPressure])


def getAndInsertStationsLimits(isDebug):
    if isDebug:
        maxValues = getMaxValues("C629X")
        maxValuesJson = dataframeToJson(maxValues)

        minValues = getMinValues("C629X")
        minValuesJson = dataframeToJson(minValues)

        avgValues = getAvgValues("C629X")
        avgValuesJson = dataframeToJson(avgValues)
    else:
        stationCount = 0
        for station in stations.collect():
            print(str(stationCount) + " : " + station.station_id)
            getAndInsertStationLimits(station.station_id)
            stationCount += 1


def prepareJson(data, pstationId):
    stationData = dataframeToJson(stations[stations.station_id == pstationId])

    stationData = json.loads(stationData)
    latitude = stationData["latitude"]["0"]
    longitude = stationData["longitude"]["0"]

    coordinates = {"lat": latitude, "lng": longitude}
    name = stationData["name"]["0"]

    calculatedData = json.loads(data)
    maxTemp = calculatedData["max_temp"]["0"]
    minTemp = calculatedData["min_temp"]["0"]
    temps = [maxTemp, minTemp]
    finalData = {"name": name, "description": temps, "coordinates": coordinates, "extra": ""}

    return finalData


if __name__ == "__main__":
    initEnvironment()
    loadData()
    finalData = []
    start_time = time.time()
    getAndInsertStationsLimits(False)
    print("--- %s seconds in total---" % (time.time() - start_time))
    print("END")
