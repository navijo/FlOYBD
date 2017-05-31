
from django.shortcuts import render
from ..models import Station

import requests
import os
import json
import time
import datetime
import simplekml

def getConcreteValues(request):
	date = request.POST['date']

	if 'station' not in request.POST:
		station_id = 0
	else:
		station_id = request.POST['station']

	getAllStations = False
	if 'allStations' not in request.POST:
		allStations = 0
	else:
		allStations = request.POST['allStations']
		getAllStations = True


	stations = Station.objects.all()

	response = requests.get('http://130.206.117.178:5000/getMeasurement?date='+date+'&station_id='+station_id+'&allStations='+str(getAllStations),stream=True)
	jsonData = json.loads(response.json())

	stationsWeather = {}
	for row in jsonData:
		concreteStation = Station.objects.get(station_id=row.get("station_id"))
		stationData = {}

		timestamp = row.get("measure_date")
		measureDate = datetime.datetime.utcfromtimestamp(float(timestamp) / 1000).strftime('%d-%m-%Y')
		contentString = '<div id="content">' + \
						'<div id="siteNotice">' + \
						'</div>' + \
						'<h1 id="firstHeading" class="firstHeading">' + concreteStation.name + '</h1>' + \
						'<h3>' + measureDate + '</h3>' + \
						'<div id="bodyContent">' + \
						'<p>' + \
						'<br/><b>Max Temp: </b>' + str(row.get("max_temp")) + \
						'<br/><b>Med Temp: </b>' + str(row.get("med_temp")) + \
						'<br/><b>Min Temp: </b>' + str(row.get("min_temp")) + \
						'<br/><b>Max Pressure: </b>' + str(row.get("max_pressure")) + \
						'<br/><b>Min Pressure: </b>' + str(row.get("min_pressure")) + \
						'<br/><b>Precip: </b>' + str(row.get("precip")) + \
						'<br/><b>Insolation: </b>' + str(row.get("insolation")) + \
						'</p>' + \
						'</div>' + \
						'</div>'
		stationData["timestamp"] = timestamp
		stationData["measureDate"] = measureDate
		stationData["contentString"] = contentString
		stationData["latitude"] = concreteStation.latitude
		stationData["longitude"] = concreteStation.longitude
		stationData["name"] = concreteStation.name
		stationsWeather[row.get("station_id")] = stationData

		if not getAllStations:
			return render(request, 'floybd/weather/weatherConcreteView.html',
						  {'stations': stations, 'concreteStation': concreteStation, 'weatherData': contentString,
						   'date': date})

	if getAllStations:
		kml = simplekml.Kml()
		for key, value in stationsWeather.items():
			kml.newpoint(name=value["name"], description=value["contentString"],
						 coords=[(value["longitude"], value["latitude"])])


		millis = int(round(time.time() * 1000))
		fileName = "measurement_" + str(date) + "_" + str(millis) + ".kml"
		currentDir = os.getcwd()
		dir1 = os.path.join(currentDir, "static/kmls")
		dirPath2 = os.path.join(dir1, fileName)

		kml.save(dirPath2)
	return render(request, 'floybd/weather/weatherConcreteView.html',
				  {'kml': 'http://localhost:8000/static/kmls/'+fileName,'date': date})

	#return render(request, 'floybd/weather/weatherConcreteView.html', {'stations': stations,'concreteStation':concreteStation,'weatherData':contentString,'date':date})


def sendConcreteValuesToLG(request):
	date = request.POST['date']
	millis = int(round(time.time() * 1000))


	allStations = request.POST.get('allStations', 0)

	if str(allStations) == str('allStations'):
		fileurl = request.POST['fileUrl']
		millis = int(round(time.time() * 1000))

		fileName = "measurement_" + str(date) + "_" + str(millis) + ".kml"
		currentDir = os.getcwd()
		dir1 = os.path.join(currentDir, "static/kmls")
		dirPath2 = os.path.join(dir1, fileName)

		response = requests.get(
			'http://130.206.117.178:5000/getAllStationsMeasurementsKML?date=' + date,stream=True)
		with open(dirPath2, 'wb') as f:
			for chunk in response.iter_content(chunk_size=1024):
				if chunk:  # filter out keep-alive new chunks
					f.write(chunk)
		sendKml(fileName)

		return render(request, 'floybd/weather/weatherConcreteView.html',
					  {'kml': fileurl, 'date': date})


	else:
		station_id = request.POST['station']

		weatherData = request.POST['weatherData']

	fileName = "measurement_" + str(date)+"_"+str(millis)+ ".kml"
	currentDir = os.getcwd()
	dir1 = os.path.join(currentDir, "static/kmls")
	dirPath2 = os.path.join(dir1, fileName)

	response = requests.get('http://130.206.117.178:5000/getMeasurementKml?date=' + date + '&station_id=' + station_id,
							stream=True)
	with open(dirPath2, 'wb') as f:
		for chunk in response.iter_content(chunk_size=1024):
			if chunk:  # filter out keep-alive new chunks
				f.write(chunk)

	stations = Station.objects.all()
	concreteStation = Station.objects.get(station_id=station_id)

	sendKml(fileName,concreteStation)


	#kmlPath = "http://localhost:8000/static/" + fileName
	return render(request, 'floybd/weather/weatherConcreteView.html',
				  {'stations': stations, 'concreteStation': concreteStation, 'weatherData':weatherData,'date': date})


def sendKml(fileName,concreteStation):
	command = "echo 'http://192.168.88.243:8000/static/kmls/"+fileName+"' | sshpass -p lqgalaxy ssh lg@192.168.88.198 'cat - > /var/www/html/kmls.txt'"
	os.system(command)

	flyTo = "flytoview=<LookAt>"\
			+"<longitude>"+str(concreteStation.longitude)+"</longitude>"\
			+"<latitude>"+str(concreteStation.latitude)+"</latitude>"\
			+"<altitude>100</altitude>"\
			+"<heading>14</heading>" \
			+"<tilt>69</tilt>"\
			+"<range>200000</range>"\
			+"<altitudeMode>relativeToGround</altitudeMode>"\
			+"<gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode></LookAt>"


	command = "echo '"+flyTo+"' | sshpass -p lqgalaxy ssh lg@192.168.88.198 'cat - > /tmp/query.txt'"
	print(command)
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
