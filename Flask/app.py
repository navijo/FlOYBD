from flask import Flask
from flask import send_from_directory
from flask import request
from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext, SparkSession

import os.path
import sys
import time
import json
import shutil

import datetime
import functools
from utils import sparkFunctions, generalFunctions

from flask import jsonify
from flask_cache import Cache

import traceback
import logging

app = Flask(__name__, static_url_path='')
cache = Cache(app, config={'CACHE_TYPE': 'simple'})


def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return (path + args).encode('utf-8')

def make_cache_key_post(*args, **kwargs):
    path = request.path
    dataStr = str(request.data, 'utf-8')
    dataDict = json.loads(dataStr)
    args = str(hash(frozenset(dataDict.items())))
    return (path + args).encode('utf-8')

def make_cache_key_earthquakes(*args, **kwargs):
    path = request.path
    date = request.args.get('date')
    max_y = request.args.get('maxY')
    min_y = request.args.get('minY')
    max_x = request.args.get('maxX')
    min_x = request.args.get('minX')
    args = str(hash(frozenset([date, max_y, min_y, max_x, min_x])))
    return (path + args).encode('utf-8')


def timing(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        logging.info('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsedTime * 1000)))

    return newfunc


@app.route('/saveAPIKey', methods=['POST'])
def saveApiKey():
    creation_date = request.form['date']
    apiKey = request.form['apiKey']
    generalFunctions.saveKEY(creation_date, apiKey)


@app.route('/saveAPIKeyGet', methods=['GET'])
def saveApiKeyGet():
    apiKey = request.args.get('key')
    creation_date = datetime.datetime.now()
    generalFunctions.saveKEY(creation_date, apiKey)
    return "Ok"


@app.route('/getKey', methods=['GET'])
def getApiKey():
    return jsonify(generalFunctions.getKey())


@app.route('/getAllStationsMeasurementsKML')
def getAllStationsMeasurementsKML():
    initEnvironment()
    loadStations()
    loadCleanDaily()
    date = request.args.get('date')
    weatherData = sparkFunctions.getConcreteWeatherData(clean_daily, '', date, "True")

    timestamp = time.time()
    fileName = "measurement_" + str(int(timestamp))
    generalFunctions.generateAllStationsKml(weatherData, stations, fileName)

    stopEnvironment(sc)
    return send_from_directory(directory='.', filename="kmls/" + fileName + ".kmz", as_attachment=True,
                               mimetype='application/octet-stream')


@app.route('/getMeasurementKml')
def getMeasurementKml():
    initEnvironment()
    loadStations()
    loadCleanDaily()

    date = request.args.get('date')
    station_id = request.args.get('station_id')

    weatherData = sparkFunctions.getConcreteWeatherData(clean_daily, station_id, date, "False")
    stationData = sparkFunctions.getStationInfo(stations, station_id)

    timestamp = time.time()
    fileName = "measurement_" + str(int(timestamp))

    generalFunctions.generateKml(weatherData, stationData, fileName)
    stopEnvironment(sc)
    return send_from_directory(directory='.', filename="kmls/" + fileName + ".kml", as_attachment=True,
                               mimetype='application/octet-stream')


@app.route('/getMeasurement')
@cache.cached(timeout=7 * 24 * 60 * 60, key_prefix=make_cache_key)
def getMeasurement():
    initEnvironment()
    loadCleanDaily()
    date = request.args.get('date')
    station_id = request.args.get('station_id')
    getAllStations = request.args.get('allStations')

    weatherData = sparkFunctions.getConcreteWeatherData(clean_daily, station_id, date, getAllStations)
    weatherJson = generalFunctions.dataFrameToJsonStr(weatherData)

    stopEnvironment(sc)
    return jsonify(weatherJson)


@timing
@app.route('/getEarthquakes')
@cache.cached(timeout=24 * 60 * 60, key_prefix=make_cache_key)
def getEarthquakes():
    initEnvironment()
    loadEarthquakes()
    date = request.args.get('date')
    max_lat = request.args.get('max_lat')
    min_lat = request.args.get('min_lat')
    max_lon = request.args.get('max_lon')
    min_lon = request.args.get('min_lon')
    
    start_time = time.time()
    earthquakesData = sparkFunctions.getConcreteEarhquakesData(earthquakes, date, max_lat, min_lat, max_lon, min_lon)
    logging.info("--- %s seconds getting the data ---" % (time.time() - start_time))
    start_time = time.time()
    earthquakesJson = generalFunctions.dataFrameToJsonStr(earthquakesData) 
    logging.info("--- %s seconds parsing the data to json---" % (time.time() - start_time))
    # earthquakesJson = earthquakesData

    stopEnvironment(sc)
    return jsonify(earthquakesJson)


@app.route('/getEarthquakesWithQuadrants')
@cache.cached(timeout=24 * 60 * 60, key_prefix=make_cache_key_earthquakes)
def getEarthquakesWithQuadrants():
    initEnvironment()
    loadEarthquakes()
    date = request.args.get('date')
    max_y = request.args.get('maxY')
    min_y = request.args.get('minY')
    max_x = request.args.get('maxX')
    min_x = request.args.get('minX')

    start_time = time.time()
    earthquakesData = sparkFunctions.getConcreteEarhquakesDataWithQuadrants(earthquakes, date, max_y, min_y, max_x, min_x)
    logging.info("--- %s seconds getting the data ---" % (time.time() - start_time))
    
    start_time = time.time()
    earthquakesJson = generalFunctions.dataFrameToJsonStr(earthquakesData)
    logging.info("--- %s seconds parsing the data to json---" % (time.time() - start_time))

    stopEnvironment(sc)
    return jsonify(earthquakesJson)




@app.route('/getPrediction', methods=['POST'])
def getPrediction():
    try:
        data = request.data
        dataStr = str(data, 'utf-8')
        dataDict = json.loads(dataStr)
        initEnvironment()
        loadStations()

        station_id = dataDict["station_id"]
        columns = dataDict['columnsToPredict']

        stationData = sparkFunctions.getStationInfo(stations, station_id)
        currentWeather = generalFunctions.getCurrentWeather(station_id)
        if (currentWeather != 0 and currentWeather):
            weatherPrediction = sparkFunctions.predict(sql, sc, columns, station_id, currentWeather)
            if (weatherPrediction):
                predictionJson = weatherPrediction
            else:
                predictionJson = "No Model"
            stopEnvironment(sc)
            return jsonify(predictionJson)
        else:
            return "No Current Weather"
        stopEnvironment(sc)
    except KeyError as ke:
        logging.error(ke)
        stopEnvironment(sc)


@app.route('/getPredictionStats', methods=['POST'])
@cache.cached(timeout=7 * 24 * 60 * 60, key_prefix=make_cache_key_post)
def getPredictionStats():
    try:
        data = request.data
        dataStr = str(data, 'utf-8')
        dataDict = json.loads(dataStr)
        initEnvironment()
        loadCleanDaily()

        station_id = dataDict["station_id"]
        fecha = dataDict['fecha']

        station_daily = clean_daily.filter(clean_daily.station_id == station_id)
        weatherPrediction = sparkFunctions.predictStats(fecha, station_id, station_daily)

        if (weatherPrediction):
            predictionJson = generalFunctions.dataFrameToJsonStr(weatherPrediction)
        else:
            predictionJson = "No Prediction"
        stopEnvironment(sc)
        return jsonify(predictionJson)
    except KeyError as ke:
        logging.error(ke)
        stopEnvironment(sc)


@app.route('/getAllStations')
@cache.cached(timeout=24 * 60 * 60, key_prefix=make_cache_key)
def getAllStations():
    initEnvironment()
    loadStations()

    timestamp = time.time()
    stationsJson = generalFunctions.dataFrameToJsonStr(stations)
    stopEnvironment(sc)
    return stationsJson

@app.route('/clearKML')
def clearKMLS():
    logging.info("Deletings kmls folder")
    shutil.rmtree('kmls')
    os.makedirs("kmls")
    return jsonify("OK")


@app.route('/getStats', methods=['POST'])
@cache.cached(timeout=7 * 24 * 60 * 60, key_prefix=make_cache_key_post)
def getStats():
    initEnvironment()

    data = request.data
    dataStr = str(data, 'utf-8')
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
                tmpDf = sparkFunctions.getLimitsForStation(stations_limits, station_id)
                returnJson = generalFunctions.dataFrameToJsonStr(tmpDf)
                stopEnvironment(sc)
                return jsonify(returnJson)
        else:
            loadCleanDaily()
            if (allStations):
                tmpDf = sparkFunctions.getLimitsAllStationsWithInterval(clean_daily, dateFrom, dateTo)
                returnJson = generalFunctions.dataFrameToJsonStr(tmpDf)
                stopEnvironment(sc)
                return jsonify(returnJson)
            else:
                tmpDf = sparkFunctions.getLimitsStationWithInterval(clean_daily, station_id, dateFrom, dateTo)
                returnJson = generalFunctions.dataFrameToJsonStr(tmpDf)
                stopEnvironment(sc)
                return jsonify(returnJson)
    except:
        logging.error("Ooops, something went wrong getting the stats")
        stopEnvironment(sc)



@app.route('/getWeatherDataInterval', methods=['POST'])
@cache.cached(timeout=7 * 24 * 60 * 60, key_prefix=make_cache_key_post)
def getWeatherDataInterval():
    initEnvironment()

    data = request.data
    dataStr = str(data, 'utf-8')
    dataDict = json.loads(dataStr)

    dateFrom = dataDict['dateFrom']
    dateTo = dataDict['dateTo']
    logging.info("From: ",dateFrom)
    logging.info("To: ",dateTo)
    station_id = dataDict['station_id']

    try:
        loadCleanDaily()
        tmpDf = sparkFunctions.getWeatherDataInterval(clean_daily, station_id, dateFrom, dateTo)
        returnJson = generalFunctions.dataFrameToJsonStr(tmpDf)
        stopEnvironment(sc)
        return jsonify(returnJson)
    except:
        logging.error("Ooops, something went wrong getting the stats")
        stopEnvironment(sc)


def loadGlobalWeatherStats():
    global stations_limits
    stations_limits = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station_limits")


def loadStations():
    global stations
    stations = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="station")


def loadCleanDaily():
    global clean_daily
    clean_daily = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev",
                                                                         table="clean_daily_measurement")


def loadEarthquakes():
    global earthquakes
    earthquakes = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="earthquake")


@app.route('/getStatsImage')
def getStatsImage():
    basePath = "/home/ubuntu/GSOC17/FlOYBD/Flask/graphs/"
    station_id = request.args.get('station_id')
    imageType = request.args.get('imageType')

    fileName = station_id + "_" + imageType

    return send_from_directory(directory=basePath + station_id, filename=fileName + ".png", as_attachment=True,
                               mimetype='image/png')


def initEnvironment():
    global sc, sql
    try:
        conf = SparkConf()
        #conf.setMaster("spark://192.168.246.236:7077")
        conf.setMaster("local[*]")
        conf.setAppName("Flask")
        conf.set("spark.cassandra.connection.host", "192.168.246.236")
        conf.set("spark.executor.memory", "10g")
        conf.set("spark.num.executors", "1")
        #conf.set("spark.driver.allowMultipleContexts", "true")

        sc = SparkContext(conf=conf)
        sql = SQLContext(sc)
        spark = SparkSession(sc)

        logging.debug("SparkContext => ", sc)
        logging.debug("SQLContext => ", sql)
    except:
        sc.stop()
        initEnvironment()


def stopEnvironment(context):
    context.stop()


if __name__ == "__main__":
    try:
        sys.path.insert(1, '/home/ubuntu/TFM/dataminingScripts/weather/ml')
        app.run(host='0.0.0.0')
        if 'sc' in globals():
            sc.stop()
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error("Oooops, something went wrong when closing the app")
        if 'sc' in globals():
            sc.stop()
