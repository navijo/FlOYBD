
from django.shortcuts import render
from ..models import Station
import simplekml
from polycircles import polycircles

import requests
import os
import json
import datetime
import shutil
import time

def getEarthquakes(request):
	print("Getting Earthquakes")
	date = request.POST['date']

	max_lat = request.POST['max_lat']
	min_lat = request.POST['min_lat']
	max_lon = request.POST['max_lon']
	min_lon = request.POST['min_lon']

	center_lat = (float(max_lat) + float(min_lat))/2
	center_lon = (float(max_lon) + float(min_lon))/2

	response = requests.get('http://130.206.117.178:5000/getEarthquakes?date='+date+'&max_lat='+max_lat+
							'&min_lat='+min_lat+'&max_lon='+max_lon+'&min_lon='+min_lon)

	jsonData = json.loads(response.json())

	print("Obtained " +str(len(jsonData)) +" earthquakes")

	millis = int(round(time.time() * 1000))
	fileUrl = createKml(jsonData,date,millis)
	#jsFile = createJSFile(jsonData)

	#return render(request, 'floybd/earthquakes/viewEarthquakes.html',{'data':strJson,'kml':fileUrl,'center_lat':center_lat,'center_lon':center_lon})

	#return render(request, 'floybd/earthquakes/viewEarthquakes.html', {'data': "http://localhost:8000/static/js/"+jsFile,'center_lat':center_lat,'center_lon':center_lon,'date':date})
	return render(request, 'floybd/earthquakes/viewEarthquakes.html',
				  {'kml': fileUrl, 'center_lat': center_lat, 'center_lon': center_lon,'date':date,'millis':millis})

def createJSFile(jsonData):
	data = {}
	data["type"] = "FeatureCollection"
	data["features"] = []

	for row in jsonData:
		geoJson = json.loads(str(row["geojson"]).replace("'", '"').replace("None", '""'))
		data["features"].append(geoJson)

	strJson = json.dumps(data)

	saveString = "eqfeed_callback(" + strJson + ");"
	jsFile = "earthquakes.js"
	currentDir = os.getcwd()
	dir1 = os.path.join(currentDir, "static/js")
	dirPath2 = os.path.join(dir1, jsFile)
	file = open(dirPath2, "w")
	file.write(saveString)
	file.close()

	return jsFile

def populateInfoWindow(row,json):
	place = row["place"]
	latitude = row["latitude"]
	longitude = row["longitude"]
	magnitude = row["magnitude"]
	fecha = row["fecha"]

	datetimeStr = datetime.datetime.fromtimestamp(int(fecha)/1000).strftime('%Y-%m-%d %H:%M:%S')

	url = json.get("properties").get("detail")
	contentString = '<div id="content">' +\
	'<div id="siteNotice">' +\
	'</div>' +\
	'<h3>Ocurred on ' + str(datetimeStr) + '</h3>' + \
	'<div id="bodyContent">' +\
	'<p>'+\
	'<br/><b>Latitude: </b>'+str(latitude)+ \
	'<br/><b>Longitude: </b>' + str(longitude) + \
	'<br/><b>Magnitude: </b>' + str(magnitude) + \
	'<br/><a href=' + str(url) + ' target="_blank">More Info</a>'\
	'</p>' +\
	'</div>' +\
	'</div>'
	return contentString

def createKml(jsonData,date,millis):
	cleanKMLS()
	kml = simplekml.Kml()

	for row in jsonData:
		place = row["place"]
		latitude = row["latitude"]
		longitude = row["longitude"]
		magnitude = row["magnitude"]
		geoJson = json.loads(str(row["geojson"]).replace("'", '"').replace("None", '""'))
		infowindow = populateInfoWindow(row,geoJson)
		#infowindow = ""
		try:
			if magnitude is not None:
				absMagnitude = abs(float(magnitude))
				color = simplekml.Color.grey
				if absMagnitude <= 2:
					color = simplekml.Color.green
				elif absMagnitude > 2 and absMagnitude <= 5:
					color = simplekml.Color.orange
				elif absMagnitude > 5:
					color = simplekml.Color.red

				polycircle = polycircles.Polycircle(latitude=latitude, longitude=longitude,
													radius=2000 * absMagnitude, number_of_vertices=36)
				pol = kml.newpolygon(name=place, description=infowindow, outerboundaryis=polycircle.to_kml())
				pol.style.polystyle.color = simplekml.Color.changealphaint(200, color)
				#pol.style.polystyle.color = simplekml.Color.rgb(255,0,0)
			else:
				kml.newpoint(name=place, description=infowindow, coords=[(longitude, latitude)])
		except ValueError:
			kml.newpoint(name=place, description=infowindow, coords=[(longitude, latitude)])
			print(absMagnitude)

	fileName = "earthquakes" + str(date)+"_" +str(millis)+ ".kml"
	currentDir = os.getcwd()
	dir1 = os.path.join(currentDir, "static/kmls")
	dirPath2 = os.path.join(dir1, fileName)
	kml.save(dirPath2)

	fileUrl = "http://localhost:8000/static/kmls/" + fileName
	return fileUrl


def sendConcreteValuesToLG(request):
	date = request.POST['date']
	millis = request.POST['millis']

	fileName = "earthquakes" + str(date) +"_" +str(millis)+ ".kml"

	sendKml(fileName)

	return render(request, 'floybd/earthquakes/viewEarthquakes.html')


def sendKml(fileName):
	command = "echo 'http://192.168.88.243:8000/static/kmls/"+fileName+"' | sshpass -p lqgalaxy ssh lg@192.168.88.198 'cat - > /var/www/html/kmls.txt'"
	os.system(command)



def cleanKMLS():

	if not os.path.exists("static/kmls"):
		print("Creating kmls folder")
		os.makedirs("static/kmls")
	else:
		print("Deletings kmls folder")
		shutil.rmtree('static/kmls')
		os.makedirs("static/kmls")