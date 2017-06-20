from utils.cylinders import CylindersKml
from utils.cylindersExt import CylindersKmlExtended
import pandas as pd
import json
import datetime
from cassandra.cluster import Cluster

from utils import sparkFunctions

from requests.packages.urllib3.exceptions import InsecureRequestWarning

import requests

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def saveKEY(date,key):
	cluster = Cluster(['192.168.246.236'])
	session = cluster.connect("dev")

	valid_date = date + datetime.timedelta(days=90)

	session.execute("TRUNCATE api_key")

	session.execute("INSERT INTO api_key (creation_date,valid_until,\"apiKey\") VALUES (%s, %s, %s)"
					,[date,valid_date, key])

def getKey():
	cluster = Cluster(['192.168.246.236'])
	session = cluster.connect("dev")
	rows = session.execute('SELECT * FROM api_key')
	apiKey = ''
	jsonList = []
	jsonData = {}
	for row in rows:
		jsonData['creation_date'] = str(row[0].strftime("%Y-%m-%d %H:%M:%S"))
		jsonData['api_key'] = row[1]
		jsonData['valid_until'] = str(row[2].strftime("%Y-%m-%d %H:%M:%S"))
		jsonList.append(jsonData)
	return jsonList

def dataframeToJson(dataFrame):
	pandas_df = dataFrame.toPandas()
	return pandas_df.to_json(orient='records',lines=True)

def dataFrameToJsonStr(dataFrame):
	pandas_df = dataFrame.toPandas()
	return pandas_df.reset_index().to_json(path_or_buf = None, orient = 'records')
	#return pandas_df.to_json(path_or_buf = None, orient = 'records')
	

def generateAllStationsWeatherKML(stations,weatherData,fileName):
	finalData = []
	weatherJsonData = dataframeToJson(weatherData)
	jsonString = ""
	for data in weatherJsonData:
		stationData = sparkFunctions.getStationInfo(stations,data.get("station_id"))
		stationJsonData = dataframeToJson(stationData)
		jsonString += prepareJson(data,stationJsonData)
	
	finalData.append(jsonString)
	cilinders = CylindersKml(fileName,finalData)
	cilinders.makeKML()

def generateAllStationsKml(weatherData,stations,fileName):
	weatherJsonData = dataFrameToJsonStr(weatherData)
	weatherJsonData = json.loads(weatherJsonData)
	finalData = []
	jsonString = []
	for row in weatherJsonData:
		stationData = sparkFunctions.getStationInfo(stations,row.get("station_id"))
		stationJsonData = dataframeToJson(stationData)
		preparedData = prepareJson(json.dumps(row),stationJsonData)
		jsonString.append(preparedData)

	finalData.append(jsonString)

	cilinders = CylindersKmlExtended(fileName,finalData)
	cilinders.makeKML()

def generateKml(weatherData,stationData,fileName):
	finalData = []
	weatherJsonData = dataframeToJson(weatherData)
	stationJsonData = dataframeToJson(stationData)
	jsonString = prepareJson(weatherJsonData,stationJsonData)

	finalData.append(jsonString)
	cilinders = CylindersKml(fileName,finalData)
	cilinders.makeKML()

def prepareJson(weatherData,stationData):
	stationData = json.loads(stationData)

	latitude = stationData["latitude"]
	longitude = stationData["longitude"]

	coordinates = {}
	coordinates["lat"] = latitude
	coordinates["lng"] = longitude
	name = stationData["name"]
	coordinatesStr = json.dumps(coordinates)

	calculatedData = json.loads(weatherData)
	#print(calculatedData)
	maxTemp = calculatedData["max_temp"]
	medTemp = calculatedData["med_temp"]
	minTemp = calculatedData["min_temp"]
	temps = []
	temps.append(maxTemp)
	temps.append(medTemp)
	temps.append(minTemp)

	finalData = {}
	finalData["name"] = name
	finalData["description"] = temps
	finalData["coordinates"] = coordinates
	finalData["extra"] = ""
	return finalData

def getCurrentWeather(station_id):
	print("Getting current weather for station: " + station_id)
	global api_key, querystring, headers, base_url
	
	jsonKey = json.loads(getKey())
	api_key = jsonKey['api_key']


	querystring = {"api_key": api_key}
	headers = {'cache-control': "no-cache"}
	base_url = "https://opendata.aemet.es/opendata"
	

	currentWeather = getData(base_url+"/api/observacion/convencional/datos/estacion/"+station_id)

	parsedCurrentWeatherJson = {}

	if(currentWeather!=0 and currentWeather is not None):	

		precip = currentWeather[0].get("prec")
		min_temp = currentWeather[0].get("tamin")
		max_temp = currentWeather[0].get("tamax")
		max_pres = currentWeather[0].get("pres")
		insolation = currentWeather[0].get("inso")

		parsedCurrentWeatherJson["station_id"] = station_id
		parsedCurrentWeatherJson["precip"] = precip
		parsedCurrentWeatherJson["max_temp"] = max_temp
		parsedCurrentWeatherJson["med_temp"] = (float(max_temp)+float(min_temp))/2
		parsedCurrentWeatherJson["min_temp"] = min_temp
		parsedCurrentWeatherJson["max_pres"] = max_pres
		parsedCurrentWeatherJson["min_pres"] = max_pres
		parsedCurrentWeatherJson["insolation"] = insolation if insolation is not None else 0


	return parsedCurrentWeatherJson
	


def getData(url):
	"""
	Make the request to the api
	"""
	try:
		response = requests.request("GET", url, headers=headers, params=querystring, verify=False)
	
		if(response):
			jsonResponse = response.json()
			if(jsonResponse.get('estado') == 200):
				link = jsonResponse.get('datos')
				data = requests.request("GET", link, verify=False)
				if(data.status_code == 200):
					return data.json()
				else:
					return 0
			elif(jsonResponse.get('estado') == 429):
				# Sleep until next minute
				printLog("####Sleeping")
				time.sleep(60)
				printLog("####Waked up!!")
				return getData(url)
	except (requests.exceptions.ConnectionError):
		printLog("####ERROR!! => Sleeping")
		time.sleep(120)
		printLog("####Waked up!!")
		return getData(url)	