
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests
import json
import time
import simplejson
from time import gmtime, strftime
from datetime import datetime, timedelta
from cassandra.cluster import Cluster

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"

def writeFile(fileName, data):
    """Write the information to a file"""
    print("###Writing file")
    with open("./"+fileName, 'w') as outfile:
        json.dump(data, outfile, indent=0, sort_keys=True)


def printLog(msg):
    print(strftime("%d-%m-%Y %H:%M:%S", gmtime()), "->", msg)


def insertIntoDB(data):
    eventId = data.get("id")
    properties = data.get("properties")
    location = data.get("geometry")
    latitude = location.get("coordinates")[1]
    longitude = location.get("coordinates")[0]
    depth = location.get("coordinates")[2]
    magnitude = properties["mag"]
    time = properties["time"]
    place = properties["place"]
    fecha =  datetime.fromtimestamp(float(properties["time"])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    geoJson = str(data)

    magnitude = float(str(magnitude).replace(",",".")) if not (magnitude==None) else None
    depth = float(str(depth).replace(",",".")) if not (depth==None) else None


    if str(place) and str(time):
        session.execute("INSERT INTO Earthquake (\"eventId\",\"place\",\"time\",\"fecha\",\"magnitude\",\"depth\",\"longitude\",\"latitude\",\"geojson\") \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)",
        [str(eventId),str(place), str(time),fecha,magnitude, depth, longitude, latitude,geoJson])


def getEarthQuakesSpain(yearFrom):

    spainMinLatitude = 36
    spainMaxLatitude = 44
    spainMinLongitude = -9
    spainMaxLongitude = 4

    startDateStr = str(yearFrom)+"-01-01"
    url = "&starttime="+startDateStr+"&minlatitude=36&maxlatitude=44&minlongitude=-9&maxlongitude=4"
    printLog("Calculating from "+str(yearFrom))

    response = requests.get(base_url+url)
    jsonData = response.json()
    for feature in jsonData.get("features"):
        properties = feature.get("properties")
        dateTime =  datetime.datetime.fromtimestamp(float(properties["time"])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        printLog("Processing :" + properties["place"]+" for: " + str(dateTime))
        insertIntoDB(feature)

    # Canarias
    canariasMinLatitude = 27
    canariasMaxLatitude = 30
    canariasMinLongitude = -18
    canariasMaxLongitude = -13
    url = "&starttime="+startDateStr+"&minlatitude=27&maxlatitude=30&minlongitude=-18&maxlongitude=-13"
    printLog("Calculating Canarias from "+str(yearFrom))

    response = requests.get(base_url+url)
    jsonData = response.json()
    for feature in jsonData.get("features"):
        properties = feature.get("properties")
        dateTime =  datetime.fromtimestamp(float(properties["time"])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        printLog("Processing :" + properties["place"]+" for: " + str(dateTime))
        insertIntoDB(feature)

def getEarthQuakesWorld(yearFrom):

    now = datetime.now()
    while(yearFrom<=now.year):
        startDateStr = str(yearFrom)+"-01-01"
        endDateStr = str(yearFrom)+"-12-31"

        try:
            getData(startDateStr,endDateStr)
        except (simplejson.scanner.JSONDecodeError):
            printLog("####ERROR!!!"+str(yearFrom))
            getDataMonthly(yearFrom)
        finally:
            yearFrom = yearFrom+1

def getDataMonthly(yearFrom):
    for i in range(1,12):
        startDateStr = str(yearFrom)+"-"+str(i)+"-01"
        endDateStr = str(yearFrom)+"-"+str((i+1)%13)+"-01"
        getData(startDateStr,endDateStr)
        time.sleep(10)


def getData(fromDate,toDate):
    url = "&starttime="+fromDate+"&endtime="+toDate
    printLog("Calculating from "+str(fromDate)+" to " + str(toDate))
  
    response = requests.get(base_url+url)
    jsonData = response.json()
    for feature in jsonData.get("features"):
        properties = feature.get("properties")
        dateTime =  datetime.fromtimestamp(float(properties["time"])/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        try:
            printLog("Processing :" + str(properties["place"])+" for: " + str(dateTime))
            insertIntoDB(feature)
        except(UnicodeEncodeError):
            printLog("Bad encoding")



# Main Function #
if __name__ == "__main__":
    cluster = Cluster(['192.168.246.236'])
    session = cluster.connect("dev")
    #getEarthQuakesSpain(1930)
    getEarthQuakesWorld(1900)
    printLog("END")
