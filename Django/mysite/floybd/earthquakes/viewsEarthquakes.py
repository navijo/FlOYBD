
from django.shortcuts import render
import simplekml
from polycircles import polycircles



import requests
import os
import json
import datetime
from datetime import timedelta
import shutil
import time
from ..utils.utils import *


def getEarthquakes(request):
    print("Getting Earthquakes")
    date = request.POST['date']
    showAllParam = request.POST.get('showAll', 0)
    showAll = showAllParam == str(1)

    max_lat = request.POST['max_lat']
    min_lat = request.POST['min_lat']
    max_lon = request.POST['max_lon']
    min_lon = request.POST['min_lon']

    center_lat = (float(max_lat) + float(min_lat))/2
    center_lon = (float(max_lon) + float(min_lon))/2

    response = requests.get('http://130.206.117.178:5000/getEarthquakes?date='+date+'&max_lat='+max_lat+
                            '&min_lat='+min_lat+'&max_lon='+max_lon+'&min_lon='+min_lon)

    jsonData = json.loads(response.json())
    numberObtained = len(jsonData)
    print("Obtained " +str(numberObtained) +" earthquakes")

    millis = int(round(time.time() * 1000))
    fileUrl = createKml(jsonData, date, millis, showAll,numberObtained)
    #jsFile = createJSFile(jsonData)

    #return render(request, 'floybd/earthquakes/viewEarthquakes.html',{'data':strJson,'kml':fileUrl,'center_lat':center_lat,'center_lon':center_lon})

    #return render(request, 'floybd/earthquakes/viewEarthquakes.html', {'data': "http://localhost:8000/static/js/"+jsFile,'center_lat':center_lat,'center_lon':center_lon,'date':date})
    return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                  {'kml': fileUrl, 'center_lat': center_lat,
                   'center_lon': center_lon, 'date': date, 'millis': millis,
                   'showAll': showAllParam})


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
        '<p>' + \
        '<br/><b>Latitude: </b>'+str(latitude) + \
        '<br/><b>Longitude: </b>' + str(longitude) + \
        '<br/><b>Magnitude: </b>' + str(magnitude) + \
        '<br/><a href=' + str(url) + ' target="_blank">More Info</a>'\
        '</p>' +\
        '</div>' +\
        '</div>'
    return contentString


def createKml(jsonData, date, millis, showAll, numberObtained):
    #cleanKMLS()
    kml = simplekml.Kml()

    tour = kml.newgxtour(name="EarthquakesTour")
    playlist = tour.newgxplaylist()

    #if numberObtained > 1000:
     #   balloonDuration = numberObtained/10000
    #else:
    #    balloonDuration = numberObtained / 1000
    balloonDuration = 1
    print("Default duration: " + str(balloonDuration))
    for row in jsonData:

        place = row["place"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        magnitude = row["magnitude"]
        fecha = row["fecha"]

        datetimeStr = datetime.datetime.fromtimestamp(int(fecha)/1000).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        fechaFin = datetime.datetime.fromtimestamp(int(fecha)/1000) + timedelta(hours=9)
        fechaFinStr = fechaFin.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        geoJson = json.loads(str(row["geojson"]).replace("'", '"').replace("None", '""'))
        infowindow = populateInfoWindow(row, geoJson)


        try:
            if magnitude is not None:
                absMagnitude = abs(float(magnitude))
                color = simplekml.Color.grey
                if absMagnitude <= 2:
                    color = simplekml.Color.green
                elif 2 < absMagnitude <= 5:
                    color = simplekml.Color.orange
                elif absMagnitude > 5:
                    color = simplekml.Color.red

                if not showAll:
                    playlist.newgxwait(gxduration=3*balloonDuration)

                polycircle = polycircles.Polycircle(latitude=latitude, longitude=longitude,
                                                    radius=2000 * absMagnitude, number_of_vertices=100)

                pol = kml.newpolygon(name=place, description=infowindow, outerboundaryis=polycircle.to_kml())
                pol.style.polystyle.color = simplekml.Color.changealphaint(200, color)
                pol.style.linestyle.color = simplekml.Color.changealphaint(200, color)

                if not showAll:
                    pol.visibility = 0

                    animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility><gx:balloonVisibility>1</gx:balloonVisibility></Placemark>'\
                        .format(pol.placemark.id)

                    #<gx:balloonVisibility>1</gx:balloonVisibility>
                    #pol.timestamp.when = datetimeStr
                    #pol.timespan.begin = datetimeStr
                    #pol.timespan.end = fechaFinStr

                    animatedupdatehide = playlist.newgxanimatedupdate(gxduration=balloonDuration)
                    animatedupdatehide.update.change = '<Placemark targetId="{0}"><visibility>0</visibility><gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                        .format(pol.placemark.id)

            else:
                earthquake = kml.newpoint(name=place,
                             description=infowindow,
                             coords=[(longitude, latitude)])
                earthquake.timestamp.when = datetimeStr

        except ValueError:
            kml.newpoint(name=place, description=infowindow, coords=[(longitude, latitude)])
            print(absMagnitude)

    if not showAll:
        playlist.newgxwait(gxduration=3)


    fileName = "earthquakes" + str(date)+"_" +str(millis)+ ".kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)
    kml.save(dirPath2)

    ip = getIp()

    fileUrl = "http://"+ip+":8000/static/kmls/" + fileName
    return fileUrl


def sendConcreteValuesToLG(request):
    date = request.POST['date']
    millis = request.POST['millis']

    showAllParam = request.POST.get('showAll', 0)
    showAll = showAllParam == str(1)

    center_lat = request.POST['center_lat']
    center_lon = request.POST['center_lon']

    ip = getIp()

    fileName = "earthquakes" + str(date) +"_" +str(millis)+ ".kml"
    fileUrl = "http://"+ip+":8000/static/kmls/" + fileName

    sendKml(fileName, center_lat,center_lon)

    if not showAll:
        #Start the tour
        time.sleep(5)
        command = "echo 'playtour=EarthquakesTour' | sshpass -p lqgalaxy ssh lg@192.168.88.198 'cat - > /tmp/query.txt'"
        os.system(command)

    return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                  {'kml': fileUrl, 'center_lat': center_lat,
                   'center_lon': center_lon, 'date': date, 'millis': millis})


def sendKml(fileName, center_lat, center_lon):
    #Javi : 192.168.88.234
    #Gerard: 192.168.88.198

    lgIp = "192.168.88.234"
    ip = getIp()

    command = "echo 'http://"+ip+":8000/static/kmls/"+fileName +\
              "' | sshpass -p lqgalaxy ssh lg@"+lgIp+" 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    flyTo = "flytoview=<LookAt>" \
            + "<longitude>" + str(center_lon) + "</longitude>" \
            + "<latitude>" + str(center_lat) + "</latitude>" \
            + "<altitude>100</altitude>" \
            + "<heading>14</heading>" \
            + "<tilt>69</tilt>" \
            + "<range>200000</range>" \
            + "<altitudeMode>relativeToGround</altitudeMode>" \
            + "<gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode>" \
            + "</LookAt>"

    command = "echo '" + flyTo + "' | sshpass -p lqgalaxy ssh lg@"+lgIp+" 'cat - > /tmp/query.txt'"
    os.system(command)


def cleanKMLS():

    if not os.path.exists("static/kmls"):
        print("Creating kmls folder")
        os.makedirs("static/kmls")
    else:
        print("Deletings kmls folder")
        shutil.rmtree('static/kmls')
        os.makedirs("static/kmls")