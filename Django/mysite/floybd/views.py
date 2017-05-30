from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
import requests
import time
import os

def index(request):
    return render(request, 'floybd/index.html')

def getConcreteKML(request):
	date = request.POST['date']
	print(date)

	timestamp =  time.time()
	fileName = "measurement_"+str(date)+".kml"
	currentDir = os.getcwd()
	dir1 = os.path.join(currentDir,"static")
	dirPath2 = os.path.join(dir1,fileName)

	response = requests.get('http://130.206.117.178:5000/getMeasurement?date='+date+'&station_id=3195',stream=True)
	with open(dirPath2, 'wb') as f:
		for chunk in response.iter_content(chunk_size=1024):
			if chunk:  # filter out keep-alive new chunks
				f.write(chunk)
	sendKml(fileName,request)
	#template = loader.get_template('floybd/index.html')
	#return HttpResponse(template.render(request))
	return render(request, 'floybd/index.html')

def sendKml(fileName,request):
	command = "echo 'http://192.168.88.243:8000/static/"+fileName+"' | sshpass -p lqgalaxy ssh lg@192.168.88.242 'cat - > /var/www/html/kmls.txt'"
	os.system(command)

