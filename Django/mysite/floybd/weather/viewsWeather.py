
from django.shortcuts import render
from ..models import Station

import requests
import os
import json
import datetime

def getConcreteValues(request):
	date = request.POST['date']
	print(date)

	station_id = request.POST['station']
	print(station_id)

	stations = Station.objects.all()
	concreteStation = Station.objects.get(station_id=station_id)

	response = requests.get('http://130.206.117.178:5000/getMeasurement?date='+date+'&station_id='+station_id,stream=True)
	jsonData = json.loads(response.json())
	print(jsonData)
	timestamp = jsonData.get("measure_date")
	measureDate = datetime.datetime.utcfromtimestamp(float(timestamp)/1000).strftime('%d-%m-%Y')

	contentString = '<div id="content">' +\
	'<div id="siteNotice">' +\
	'</div>' +\
	'<h1 id="firstHeading" class="firstHeading">'+concreteStation.name+'</h1>' + \
	'<h3>' + measureDate + '</h3>' + \
	'<div id="bodyContent">' +\
	'<p>'+\
	'<br/><b>Max Temp: </b>'+str(jsonData.get("max_temp"))+ \
	'<br/><b>Med Temp: </b>' + str(jsonData.get("med_temp")) + \
	'<br/><b>Min Temp: </b>' + str(jsonData.get("min_temp")) + \
	'<br/><b>Max Pressure: </b>' + str(jsonData.get("max_pressure")) + \
	'<br/><b>Min Pressure: </b>' + str(jsonData.get("min_pressure")) + \
	'<br/><b>Precip: </b>' + str(jsonData.get("precip")) + \
	'<br/><b>Insolation: </b>' + str(jsonData.get("insolation")) + \
	'</p>' +\
	'</div>' +\
	'</div>'




	return render(request, 'floybd/weather/weatherConcreteView.html', {'stations': stations,'concreteStation':concreteStation,'weatherData':contentString,'date':date})


def sendConcreteValuesToLG(request):
	date = request.POST['date']
	print(date)

	station_id = request.POST['station']
	print(station_id)

	weatherData = request.POST['weatherData']

	fileName = "measurement_" + str(date) + ".kml"
	currentDir = os.getcwd()
	dir1 = os.path.join(currentDir, "static")
	dirPath2 = os.path.join(dir1, fileName)

	response = requests.get('http://130.206.117.178:5000/getMeasurementKml?date=' + date + '&station_id=' + station_id,
							stream=True)
	with open(dirPath2, 'wb') as f:
		for chunk in response.iter_content(chunk_size=1024):
			if chunk:  # filter out keep-alive new chunks
				f.write(chunk)
	sendKml(fileName, request)

	stations = Station.objects.all()
	concreteStation = Station.objects.get(station_id=station_id)
	#kmlPath = "http://localhost:8000/static/" + fileName
	return render(request, 'floybd/weather/weatherConcreteView.html',
				  {'stations': stations, 'concreteStation': concreteStation, 'weatherData':weatherData,'date': date})


def sendKml(fileName, request):
	command = "echo 'http://192.168.88.243:8000/static/"+fileName+"' | sshpass -p lqgalaxy ssh lg@192.168.88.242 'cat - > /var/www/html/kmls.txt'"
	os.system(command)


def weatherConcreteIndex(request):
	stations = Station.objects.all()
	return render(request, 'floybd/weather/weatherConcrete.html', {'stations': stations})


def weatherPredictions(request):
	stations = Station.objects.all()
	columnsList = ["max_temp", "med_temp", "min_temp", "max_pressure", "min_pressure", "precip", "insolation"]
	return render(request, 'floybd/weather/weatherPrediction.html',  {'stations': stations,'columnsList':columnsList})


def getPrediction(request):
	stations = Station.objects.all()
	columnsList = ["max_temp", "med_temp", "min_temp", "max_pressure", "min_pressure", "precip", "insolation"]

	station_id = request.POST['station']
	columnsToPredict = request.POST.getlist('columnToPredict')
	print(columnsToPredict)

	jsonData = {}
	jsonData["station_id"] = station_id
	jsonData["columnsToPredict"] = columnsToPredict
	payload = json.dumps(jsonData)

	response = requests.post('http://130.206.117.178:5000/getPrediction',
							 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
							 data=payload)
	print(response.text)
	result = json.loads(response.text)
	return render(request, 'floybd/weather/weatherPrediction.html', {'result':result,'stations': stations, 'columnsList': columnsList})
