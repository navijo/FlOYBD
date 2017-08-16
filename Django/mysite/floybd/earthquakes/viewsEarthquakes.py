import logging
import requests
from django.shortcuts import render
from ..utils.lgUtils import *
from ..utils.earthquakesUtils import *
from ..utils.cylinders.cylindersHeatMap import *
from django.http import HttpResponse
from json.decoder import JSONDecodeError

logger = logging.getLogger("django")


def getEarthquakesExact(request):
    start_time = time.time()

    logger.info("Getting Earthquakes")
    date = request.POST['date']
    createTourParam = request.POST.get('createTour', 0)
    createTour = createTourParam == str(1)

    sparkIp = getSparkIp()

    max_lat = request.POST['max_lat']
    min_lat = request.POST['min_lat']
    max_lon = request.POST['max_lon']
    min_lon = request.POST['min_lon']

    center_lat = (float(max_lat) + float(min_lat)) / 2
    center_lon = (float(max_lon) + float(min_lon)) / 2
    try:
        response = requests.get('http://' + sparkIp + ':5000/getEarthquakes?date=' + date + '&max_lat=' + max_lat +
                                '&min_lat=' + min_lat + '&max_lon=' + max_lon + '&min_lon=' + min_lon)
        jsonData = json.loads(response.json())
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')
    except JSONDecodeError:
        return render(request, '500.html')

    numberObtained = len(jsonData)
    logging.info("Obtained " + str(numberObtained) + " earthquakes")

    logger.debug("--- %s getting the data---" % (time.time() - start_time))

    if numberObtained == 0:
        return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                      {'noData': True})

    start_time = time.time()

    millis = int(round(time.time() * 1000))
    fileUrl = createKml(jsonData, date, millis, createTour, numberObtained, request)

    logger.debug("--- %s seconds creating KML---" % (time.time() - start_time))

    return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                  {'kml': fileUrl, 'center_lat': center_lat,
                   'center_lon': center_lon, 'date': date, 'millis': millis,
                   'createTour': createTourParam})


def getEarthquakesApprox(request):
    start_time = time.time()
    logger.info("Getting Earthquakes with quadrants")
    date = request.POST['date']
    createTourParam = request.POST.get('createTour', 0)
    createTour = createTourParam == str(1)

    sparkIp = getSparkIp()

    max_lat = request.POST['max_lat']
    min_lat = request.POST['min_lat']

    maxY = getYQuadrant(float(max_lat))
    minY = getYQuadrant(float(min_lat))

    if minY > maxY:
        tmpAux = minY
        minY = maxY
        maxY = tmpAux

    max_lon = request.POST['max_lon']
    min_lon = request.POST['min_lon']

    maxX = getXQuadrant(float(max_lon))
    minX = getXQuadrant(float(min_lon))

    if minX > maxX:
        tmpAux = minX
        minX = maxX
        maxX = tmpAux

    center_lat = (float(max_lat) + float(min_lat)) / 2
    center_lon = (float(max_lon) + float(min_lon)) / 2
    logger.debug("maxY: ", maxY)
    logger.debug("minY: ", minY)
    logger.debug("maxX: ", maxX)
    logger.debug("minX: ", minX)
    try:
        response = requests.get('http://' + sparkIp + ':5000/getEarthquakesWithQuadrants?date=' + date
                                + '&maxY=' + str(maxY)
                                + '&minY=' + str(minY)
                                + '&maxX=' + str(maxX)
                                + '&minX=' + str(minX))
        jsonData = json.loads(response.json())
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')
    except JSONDecodeError:
        return render(request, '500.html')

    numberObtained = len(jsonData)
    logger.info("Obtained " + str(numberObtained) + " earthquakes")
    logger.debug("--- %s getting the data---" % (time.time() - start_time))
    if numberObtained == 0:
        return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                      {'noData': True})

    start_time = time.time()
    millis = int(round(time.time() * 1000))
    fileUrl = createKml(jsonData, date, millis, createTour, numberObtained, request)

    logger.debug("--- %s seconds creating KML---" % (time.time() - start_time))

    return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                  {'kml': fileUrl, 'center_lat': center_lat,
                   'center_lon': center_lon, 'date': date, 'millis': millis,
                   'createTour': createTourParam})


def getHeatMap(request):
    logging.info("Getting Heat Map")
    date = request.POST['date']

    sparkIp = getSparkIp()
    try:
        response = requests.get('http://' + sparkIp + ':5000/getEarthquakes?date=' + date)
        jsonData = json.loads(response.json())
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')
    except JSONDecodeError:
        return render(request, '500.html')

    numberObtained = len(jsonData)
    logging.info("Obtained " + str(numberObtained) + " earthquakes")

    if numberObtained == 0:
        return render(request, 'floybd/earthquakes/viewEarthquakesHeatMap.html',
                      {'noData': True})

    data = getEartquakesArray(jsonData, False)

    return render(request, 'floybd/earthquakes/viewEarthquakesHeatMap.html', {'data': data, 'date': date,
                                                                              'numberObtained': numberObtained})


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
    logging.info("Generating HeatMap")
    date = request.POST['date']
    millis = int(round(time.time() * 1000))
    try:
        response = requests.get('http://' + getSparkIp() + ':5000/getEarthquakes?date=' + date)
        jsonData = json.loads(response.json())
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')
    except JSONDecodeError:
        return render(request, '500.html')

    dataMapsJs = getEartquakesArray(jsonData, False)
    numberObtained = len(jsonData)
    logging.info("Obtained " + str(numberObtained) + " earthquakes")

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

    command = "echo 'http://" + getDjangoIp() + ":" + getDjangoPort(request) + \
              "/static/demos/lastWeekEarthquakesHeatMap.kmz?a=" + str(millis) + \
              "\n'http://" + getDjangoIp() + ":" + getDjangoPort(request) + \
              "/static/demos/WorldTour.kmz?a=" + str(millis) + " | sshpass -p " + getLGPass() \
              + " ssh lg@" + getLGIp() + " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)
    time.sleep(2)
    sendFlyToToLG(20.21078636181624, -111.3376967642952, 0, 1.372480247294665, 0, 14562650.06788917, 2)
    time.sleep(2)
    playTour("WorldTour")

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
    contentString = '<link rel = "stylesheet" href = ' \
                    '"https://code.getmdl.io/1.3.0/material.blue_grey-red.min.css" / > ' + \
                    '<link rel="stylesheet" href="https://fonts.googleapis.com/css?' \
                    'family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&lang=en"/>' + \
                    '<table width="560" style="font-family: Roboto;"><tr><td>' + \
                    '<div id="content">' + '<div id="siteNotice">' + '</div>' + \
                    '<h1 id="firstHeading" class="thirdHeading" style="text-align:center">' + \
                    str(row["place"]) + '</h1>' + \
                    '<h3 id="firstHeading" class="thirdHeading" style="text-align:center">Ocurred on: ' + \
                    str(datetimeStr) + '</h3>' + \
                    '<div id="bodyContent" style="text-align: center;">' + \
                    '<div class="demo-charts mdl-color--white mdl-shadow--2dp mdl-cell' \
                    ' mdl-cell--6-col mdl-grid" style="width: 98%">' + \
                    '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                    '<p style="font-size:1.5em;color:#474747;line-height:0.5;"><b>Latitude</b>:</p>' + \
                    '</div>' + \
                    '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                    '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + str(latitude) + '</p>' + \
                    '</div>' + \
                    '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                    '<p style="font-size:1.5em;color:#474747;line-height:0.5;"><b>Longitude</b>:</p>' + \
                    '</div>' + \
                    '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                    '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + str(longitude) + '</p>' + \
                    '</div>' + \
                    '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                    '<p style="font-size:1.5em;color:#474747;line-height:0.5;"><b>Magnitude</b>:</p>' + \
                    '</div>' + \
                    '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                    '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + str(magnitude) + '</p>' + \
                    '</div>' + \
                    '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                    '<p style="font-size:1.5em;color:#474747;line-height:0.5;">More Info :</p>' + \
                    '</div>' + \
                    '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                    '<p style="font-size:1.5em;color:#474747;line-height:0.5;"><a href=' + str(url) + \
                    ' target="_blank">USGS</a></p>' + \
                    '</div>' + \
                    '</div>' + \
                    '</div></div>' + \
                    '</td></tr></table>'

    return contentString


def createKml(jsonData, date, millis, createTour, numberObtained, request):
    kml = simplekml.Kml()

    tour = kml.newgxtour(name="EarthquakesTour")
    playlist = tour.newgxplaylist()
    flyToDuration = 3
    balloonDuration = 1
    if numberObtained > 1000:
        balloonDuration = numberObtained/1000

    logging.info("Default duration: " + str(balloonDuration))
    for row in jsonData:

        place = row["place"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        magnitude = row["magnitude"]
        fecha = row["fecha"]

        datetimeStr = datetime.datetime.fromtimestamp(int(fecha) / 1000).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        try:
            geoJson = replaceJsonString(str(row["geojson"]))
            infowindow = populateInfoWindow(row, geoJson)
        except JSONDecodeError:
            logging.error('Error decoding json')
            logging.error(str(row["geojson"]))
            continue
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

                if createTour:
                    playlist.newgxwait(gxduration=3 * balloonDuration)

                polycircle = polycircles.Polycircle(latitude=latitude, longitude=longitude,
                                                    radius=2000 * absMagnitude, number_of_vertices=100)

                pol = kml.newpolygon(name="", description=infowindow, outerboundaryis=polycircle.to_kml())
                pol.style.polystyle.color = color
                pol.style.polystyle.fill = 0
                pol.style.polystyle.outline = 1
                pol.style.linestyle.color = color
                pol.style.linestyle.width = 10
                pol.style.balloonstyle.bgcolor = simplekml.Color.lightblue
                pol.style.balloonstyle.text = "$[description]"

                if createTour:
                    pol.visibility = 0
                    # Fly To the atmosphere
                    flyto = playlist.newgxflyto(gxduration=flyToDuration,
                                                gxflytomode=simplekml.GxFlyToMode.smooth)
                    flyto.camera.longitude = longitude
                    flyto.camera.latitude = latitude
                    flyto.camera.altitude = 15000000
                    flyto.camera.range = 15000000
                    flyto.camera.tilt = 0
                    playlist.newgxwait(gxduration=flyToDuration)

                    # Go Back To the point
                    flyto = playlist.newgxflyto(gxduration=flyToDuration,
                                                gxflytomode=simplekml.GxFlyToMode.smooth)
                    flyto.camera.longitude = longitude
                    flyto.camera.latitude = latitude
                    flyto.camera.altitude = 100000
                    flyto.camera.range = 100000
                    flyto.camera.tilt = 0
                    playlist.newgxwait(gxduration=flyToDuration)

                    simulateEarthquake(playlist, latitude, longitude, absMagnitude)

                    animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration / 10)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}">' \
                                                       '<visibility>1</visibility></Placemark>' \
                        .format(pol.placemark.id)

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
                        polAux.style.balloonstyle.displaymode = simplekml.DisplayMode.hide

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

                    playlist.newgxwait(gxduration=10)

                    animatedupdatehide = playlist.newgxanimatedupdate(gxduration=balloonDuration*2)
                    animatedupdatehide.update.change = '<Placemark targetId="{0}">' \
                                                       '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                        .format(pol.placemark.id)
                else:
                    pol.visibility = 1
            else:
                earthquake = kml.newpoint(name=place,
                                          description=infowindow,
                                          coords=[(longitude, latitude)])
                earthquake.timestamp.when = datetimeStr

        except ValueError:
            kml.newpoint(name=place, description=infowindow, coords=[(longitude, latitude)])
            logging.error(str(absMagnitude))

    if createTour:
        playlist.newgxwait(gxduration=3 * balloonDuration)

    fileName = "earthquakes" + str(date) + "_" + str(millis) + ".kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)
    logging.info("Saving kml: ", dirPath2)
    kml.save(dirPath2)

    ip = getDjangoIp()

    fileUrl = "http://" + ip + ":"+getDjangoPort(request)+"/static/kmls/" + fileName
    return fileUrl


def createKmz(jsonData, date, millis, createTour, numberObtained, request):
    kml = simplekml.Kml()

    tour = kml.newgxtour(name="EarthquakesTour")
    playlist = tour.newgxplaylist()

    balloonDuration = 1
    flyToDuration = 3

    if numberObtained > 1000:
        balloonDuration = numberObtained/1000

    logging.info("Default duration: " + str(balloonDuration))
    for row in jsonData:

        place = row["place"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        magnitude = row["magnitude"]
        fecha = row["fecha"]

        datetimeStr = datetime.datetime.fromtimestamp(int(fecha) / 1000).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        try:
            geoJson = replaceJsonString(str(row["geojson"]))
            infowindow = populateInfoWindow(row, geoJson)
        except JSONDecodeError:
            logging.error('Error decoding json')
            logging.error(str(row["geojson"]))
            continue

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

                if createTour:
                    playlist.newgxwait(gxduration=3 * balloonDuration)

                polycircle = polycircles.Polycircle(latitude=latitude, longitude=longitude,
                                                    radius=2000 * absMagnitude, number_of_vertices=100)

                pol = kml.newpolygon(name="", description=infowindow, outerboundaryis=polycircle.to_kml())

                pol.style.polystyle.color = color
                pol.style.polystyle.fill = 0
                pol.style.polystyle.outline = 1

                pol.style.linestyle.color = color
                pol.style.linestyle.width = 10
                pol.style.balloonstyle.bgcolor = simplekml.Color.lightblue
                pol.style.balloonstyle.text = "$[description]"

                if createTour:
                    pol.visibility = 0
                    # Fly To the atmosphere
                    flyto = playlist.newgxflyto(gxduration=flyToDuration,
                                                gxflytomode=simplekml.GxFlyToMode.smooth)
                    flyto.camera.longitude = longitude
                    flyto.camera.latitude = latitude
                    flyto.camera.altitude = 15000000
                    flyto.camera.range = 15000000
                    flyto.camera.tilt = 0
                    playlist.newgxwait(gxduration=flyToDuration)

                    # Go Back To the point
                    flyto = playlist.newgxflyto(gxduration=flyToDuration,
                                                gxflytomode=simplekml.GxFlyToMode.smooth)
                    flyto.camera.longitude = longitude
                    flyto.camera.latitude = latitude
                    flyto.camera.altitude = 100000
                    flyto.camera.range = 100000
                    flyto.camera.tilt = 0
                    playlist.newgxwait(gxduration=flyToDuration)

                    simulateEarthquake(playlist, latitude, longitude, absMagnitude)

                    animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration / 10)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}">' \
                                                       '<visibility>1</visibility></Placemark>' \
                        .format(pol.placemark.id)

                    for i in range(1, 11):
                        polycircleAux = polycircles.Polycircle(latitude=latitude, longitude=longitude,
                                                               radius=(200 * i) * absMagnitude, number_of_vertices=100)

                        polAux = kml.newpolygon(name="", outerboundaryis=polycircleAux.to_kml())
                        polAux.style.polystyle.color = color
                        polAux.style.polystyle.fill = 1
                        polAux.style.polystyle.outline = 1
                        polAux.style.linestyle.color = color
                        polAux.style.linestyle.width = 1
                        polAux.visibility = 0
                        polAux.style.balloonstyle.displaymode = simplekml.DisplayMode.hide

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

                    playlist.newgxwait(gxduration=10)

                    animatedupdatehide = playlist.newgxanimatedupdate(gxduration=balloonDuration*2)
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
            logging.error(absMagnitude)

    if createTour:
        playlist.newgxwait(gxduration=3 * balloonDuration)

    fileName = "earthquakes" + str(date) + "_" + str(millis) + ".kmz"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)
    logging.info("Saving kmz: ", dirPath2)
    kml.savekmz(dirPath2, format=False)

    ip = getDjangoIp()

    fileUrl = "http://" + ip + ":"+getDjangoPort(request)+"/static/kmls/" + fileName
    return fileUrl


def sendConcreteValuesToLG(request):
    date = request.POST['date']
    millis = request.POST['millis']

    createTourParam = request.POST.get('createTour', 0)
    createTour = createTourParam == str(1)

    center_lat = request.POST['center_lat']
    center_lon = request.POST['center_lon']

    ip = getDjangoIp()

    fileName = "earthquakes" + str(date) + "_" + str(millis) + ".kml"
    fileUrl = "http://" + ip + ":"+getDjangoPort(request)+"/static/kmls/" + fileName

    sendKmlToLG(fileName, request)

    sendFlyToToLG(center_lat, center_lon, 100, 14, 69, 200000, 2)

    if createTour:
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/kmls")
        dirPath2 = os.path.join(dir1, fileName)
        fileBytes = os.path.getsize(dirPath2)
        megas = (fileBytes/1024)/1000

        logging.info("Size of the KML:" + str(os.path.getsize(dirPath2)))
        waitTime = megas/10
        logging.info("Waiting to start the tour..."+str(waitTime)+" seconds")
        time.sleep(waitTime)
        logging.info("Starting the tour!")
        playTour("EarthquakesTour")

    return render(request, 'floybd/earthquakes/viewEarthquakes.html',
                  {'kml': fileUrl, 'center_lat': center_lat,
                   'center_lon': center_lon, 'date': date, 'millis': millis})


def demoLastWeekEarthquakesHeatmap(request):
    millis = int(round(time.time() * 1000))

    command = "echo 'http://" + getDjangoIp() + ":" + getDjangoPort(request) + \
              "/static/demos/lastWeekEarthquakesHeatMap.kmz?a=" + str(millis) + \
              "\n'http://" + getDjangoIp() + ":" + getDjangoPort(request) + \
              "/static/demos/WorldTour.kmz?a=" + str(millis)+" | sshpass -p " + getLGPass() \
              + " ssh lg@" + getLGIp() + " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)
    time.sleep(2)
    sendFlyToToLG(20.21078636181624, -111.3376967642952, 0, 1.372480247294665, 0, 14562650.06788917, 2)
    time.sleep(2)
    playTour("WorldTour")
    return HttpResponse(status=204)


def demoLastWeekEarthquakes(request):
    sendDemoKmlToLG("lastWeekEarthquakes.kmz", request)
    time.sleep(10)
    playTour("LastWeekEarthquakesTour")
    return HttpResponse(status=204)


def simulateEarthquake(playlist, latitude, longitude, magnitude):
    for i in range(0, int(10*magnitude)):
        bounce = 5 if (i % 2 == 0) else 0
        flyto = playlist.newgxflyto(gxduration=0.01)
        flyto.camera.longitude = longitude
        flyto.camera.latitude = latitude
        flyto.camera.altitude = 150000
        flyto.camera.range = 150000
        flyto.camera.tilt = bounce
        playlist.newgxwait(gxduration=0.01)
