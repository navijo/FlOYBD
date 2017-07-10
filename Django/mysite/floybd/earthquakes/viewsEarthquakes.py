import datetime
import json
import time
from datetime import timedelta
import requests
from django.shortcuts import render
from ..utils.lgUtils import *
from ..utils.cylinders.cylindersHeatMap import *


def getEarthquakes(request):
    print("Getting Earthquakes")
    date = request.POST['date']
    showAllParam = request.POST.get('showAll', 0)
    showAll = showAllParam == str(1)

    sparkIp = getSparkIp()

    max_lat = request.POST['max_lat']
    min_lat = request.POST['min_lat']
    max_lon = request.POST['max_lon']
    min_lon = request.POST['min_lon']

    center_lat = (float(max_lat) + float(min_lat)) / 2
    center_lon = (float(max_lon) + float(min_lon)) / 2

    response = requests.get('http://' + sparkIp + ':5000/getEarthquakes?date=' + date + '&max_lat=' + max_lat +
                            '&min_lat=' + min_lat + '&max_lon=' + max_lon + '&min_lon=' + min_lon)

    jsonData = json.loads(response.json())
    numberObtained = len(jsonData)
    print("Obtained " + str(numberObtained) + " earthquakes")

    if numberObtained == 0:
        return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                      {'noData': True})

    millis = int(round(time.time() * 1000))
    fileUrl = createKml(jsonData, date, millis, showAll, numberObtained)

    return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                  {'kml': fileUrl, 'center_lat': center_lat,
                   'center_lon': center_lon, 'date': date, 'millis': millis,
                   'showAll': showAllParam})


def getHeatMap(request):
    print("Getting Heat Map")
    date = request.POST['date']

    sparkIp = getSparkIp()

    response = requests.get('http://' + sparkIp + ':5000/getEarthquakes?date=' + date)

    jsonData = json.loads(response.json())
    numberObtained = len(jsonData)
    print("Obtained " + str(numberObtained) + " earthquakes")

    if numberObtained == 0:
        return render(request, 'floybd/earthquakes/viewEarthquakesHeatMap.html',
                      {'noData': True})

    data = getEartquakesArray(jsonData, False)

    return render(request, 'floybd/earthquakes/viewEarthquakesHeatMap.html', {'data': data, 'date': date,
                                                                              'numberObtained':numberObtained})


def getEartquakesArray(jsonData, includeDescription):
    data = []
    for row in jsonData:
        if includeDescription:
            data.append([row.get("latitude"), row.get("longitude"), row.get("magnitude"), row.get("place"),
                         row.get("fecha")])
        else:
            data.append([row.get("latitude"), row.get("longitude"), row.get("magnitude")])

    return data


def generateHeapMapKml(request):
    print("Generating HeatMap")
    date = request.POST['date']
    dataMapsJs = request.POST['data']
    millis = int(round(time.time() * 1000))

    response = requests.get('http://' + getSparkIp() + ':5000/getEarthquakes?date=' + date)

    jsonData = json.loads(response.json())
    numberObtained = len(jsonData)
    print("Obtained " + str(numberObtained) + " earthquakes")

    if numberObtained == 0:
        return render(request, 'floybd/earthquakes/viewEarthquakesHeatMap.html',
                      {'noData': True})

    data = getEartquakesArray(jsonData, True)

    fileName = "earthquakesHeatMap_" + str(date) + "_" + str(millis) + ".kmz"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)

    cylinder = CylindersKmlHeatmap(fileName, data)
    cylinder.makeKMZ(dirPath2)
    sendKmlToLG(fileName)
    time.sleep(2)
    sendFlyToToLG(36.778259, -119.417931, 22000000, 0, 0, 22000000, 2)

    return render(request, 'floybd/earthquakes/viewEarthquakesHeatMap.html', {'data': dataMapsJs, 'date': date,
                                                                              'numberObtained': numberObtained})


def createJSFile(jsonData, millis):
    data = {"type": "FeatureCollection", "features": []}

    for row in jsonData:
        geoJson = json.dumps(row.get("geojson"))
        replacedCommas = json.loads(geoJson).replace("'", '"').replace("None", '""')
        data["features"].append(replacedCommas)

    strJson = json.dumps(data)

    saveString = "eqfeed_callback(" + strJson + ");"
    jsFile = "earthquakes_"+str(millis)+".js"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/js")
    dirPath2 = os.path.join(dir1, jsFile)
    file = open(dirPath2, "w")
    file.write(saveString)
    file.close()

    return jsFile


def populateInfoWindow(row, jsonData):
    latitude = row["latitude"]
    longitude = row["longitude"]
    magnitude = row["magnitude"]
    fecha = row["fecha"]

    datetimeStr = datetime.datetime.fromtimestamp(int(fecha) / 1000).strftime('%Y-%m-%d %H:%M:%S')

    url = jsonData.get("properties").get("detail")
    contentString = '<div id="content">' + \
                    '<div id="siteNotice">' + \
                    '</div>' + \
                    '<h3>Ocurred on ' + str(datetimeStr) + '</h3>' + \
                    '<div id="bodyContent">' + \
                    '<p>' + \
                    '<br/><b>Latitude: </b>' + str(latitude) + \
                    '<br/><b>Longitude: </b>' + str(longitude) + \
                    '<br/><b>Magnitude: </b>' + str(magnitude) + \
                    '<br/><a href=' + str(url) + ' target="_blank">More Info</a>' \
                                                 '</p>' + \
                    '</div>' + \
                    '</div>'
    return contentString


def createKml(jsonData, date, millis, showAll, numberObtained):
    kml = simplekml.Kml()

    tour = kml.newgxtour(name="EarthquakesTour")
    playlist = tour.newgxplaylist()

    balloonDuration = 1
    if numberObtained > 1000:
        balloonDuration = numberObtained/1000

    print("Default duration: " + str(balloonDuration))
    for row in jsonData:

        place = row["place"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        magnitude = row["magnitude"]
        fecha = row["fecha"]

        datetimeStr = datetime.datetime.fromtimestamp(int(fecha) / 1000).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        fechaFin = datetime.datetime.fromtimestamp(int(fecha) / 1000) + timedelta(hours=9)
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
                    playlist.newgxwait(gxduration=3 * balloonDuration)

                polycircle = polycircles.Polycircle(latitude=latitude, longitude=longitude,
                                                    radius=2000 * absMagnitude, number_of_vertices=100)

                pol = kml.newpolygon(name=place, description=infowindow, outerboundaryis=polycircle.to_kml())
                #pol.style.polystyle.color = simplekml.Color.changealphaint(200, color)
                pol.style.polystyle.color = color
                pol.style.polystyle.fill = 0
                pol.style.polystyle.outline = 1
                #pol.style.linestyle.color = simplekml.Color.changealphaint(200, color)
                pol.style.linestyle.color = color
                pol.style.linestyle.width = 10

                #pol.tessellate = 1

                if not showAll:
                    pol.visibility = 1

                    flyto = playlist.newgxflyto(gxduration=balloonDuration, gxflytomode=simplekml.GxFlyToMode.smooth)
                    flyto.camera.longitude = longitude
                    flyto.camera.latitude = latitude
                    flyto.camera.altitude = 100000
                    #flyto.camera.tilt = 20
                    playlist.newgxwait(gxduration=balloonDuration)

                    for i in range(1, 11):
                        polycircleAux = polycircles.Polycircle(latitude=latitude, longitude=longitude,
                                                               radius=(200 * i) * absMagnitude, number_of_vertices=100)

                        polAux = kml.newpolygon(name=place, outerboundaryis=polycircleAux.to_kml())
                        polAux.style.polystyle.color = color
                        polAux.style.polystyle.fill = 1
                        polAux.style.polystyle.outline = 1
                        polAux.style.linestyle.color = color
                        polAux.style.linestyle.width = 1
                        polAux.visibility = 0

                        animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration/10)
                        animatedupdateshow.update.change = '<Placemark targetId="{0}">' \
                                                           '<visibility>1</visibility></Placemark>' \
                            .format(polAux.placemark.id)

                        animatedupdatehide = playlist.newgxanimatedupdate(gxduration=balloonDuration/10)
                        animatedupdatehide.update.change = '<Placemark targetId="{0}">' \
                                                           '<visibility>0</visibility></Placemark>' \
                            .format(polAux.placemark.id)

                        playlist.newgxwait(gxduration=balloonDuration/10)

                    animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration*2)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                                       '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
                        .format(pol.placemark.id)

                    animatedupdatehide = playlist.newgxanimatedupdate(gxduration=balloonDuration*2)
                    #animatedupdatehide.update.change = '<Placemark targetId="{0}"><visibility>0</visibility><gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                    animatedupdatehide.update.change = '<Placemark targetId="{0}">' \
                                                       '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
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
        playlist.newgxwait(gxduration=3 * balloonDuration)

    fileName = "earthquakes" + str(date) + "_" + str(millis) + ".kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)
    print("Saving kml: ", dirPath2)
    kml.save(dirPath2)

    ip = getDjangoIp()

    fileUrl = "http://" + ip + ":8000/static/kmls/" + fileName
    return fileUrl


def sendConcreteValuesToLG(request):
    date = request.POST['date']
    millis = request.POST['millis']

    showAllParam = request.POST.get('showAll', 0)
    showAll = showAllParam == str(1)

    center_lat = request.POST['center_lat']
    center_lon = request.POST['center_lon']

    ip = getDjangoIp()

    fileName = "earthquakes" + str(date) + "_" + str(millis) + ".kml"
    fileUrl = "http://" + ip + ":8000/static/kmls/" + fileName

    sendKmlToLG(fileName)

    sendFlyToToLG(center_lat, center_lon, 100, 14, 69, 200000, 2)

    if not showAll:
        # Start the tour
        time.sleep(5)
        playTour("EarthquakesTour")

    return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                  {'kml': fileUrl, 'center_lat': center_lat,
                   'center_lon': center_lon, 'date': date, 'millis': millis})


