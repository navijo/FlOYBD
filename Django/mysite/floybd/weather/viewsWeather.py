from requests.packages.urllib3.exceptions import InsecureRequestWarning
from django.shortcuts import render
from ..models import Station
from ..models import ApiKey
import requests
import json
import datetime
from datetime import timedelta
from ..utils.lgUtils import *
from django.http import JsonResponse, HttpResponse
from collections import defaultdict
from simplejson.scanner import JSONDecodeError
from django.core.urlresolvers import resolve

import logging
logger = logging.getLogger("django")


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def getConcreteValues(request):
    logger.info("Getting Concrete Weather values")
    date = request.POST['date']
    station_id = request.POST.get('station', 0)
    allStations = request.POST.get('allStations', 0)

    sparkIp = getSparkIp()
    ip = getDjangoIp()

    getAllStations = allStations == str(1)

    stations = Station.objects.all()

    try:
        response = requests.get(
            'http://' + sparkIp + ':5000/getMeasurement?date=' + date + '&station_id=' + station_id +
            '&allStations=' + str(getAllStations), stream=True)
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')

    try:
        jsonData = json.loads(response.json())

        stationsWeather = {}
        if len(jsonData) == 0:
            return render(request, 'floybd/weather/weatherConcreteView.html',
                          {'noData': True, 'date': date})

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

        if getAllStations:
            kml = simplekml.Kml()
            for key, value in stationsWeather.items():
                kml.newpoint(name=value["name"], description=value["contentString"],
                             coords=[(value["longitude"], value["latitude"])])

            fileName = "measurement_" + str(date) + ".kml"
            currentDir = os.getcwd()
            dir1 = os.path.join(currentDir, "static/kmls")
            dirPath2 = os.path.join(dir1, fileName)

            kml.save(dirPath2)
            return render(request, 'floybd/weather/weatherConcreteView.html',
                          {'kml': 'http://' + ip + ':'+getDjangoPort(request)+'/static/kmls/' + fileName, 'date': date})
        else:
            concreteStation = Station.objects.get(station_id=station_id)
            contentString = stationsWeather[station_id]["contentString"]
            return render(request, 'floybd/weather/weatherConcreteView.html',
                          {'stations': stations, 'concreteStation': concreteStation,
                           'weatherData': contentString, 'date': date})
    except JSONDecodeError:
        return render(request, '500.html')


def sendConcreteValuesToLG(request):
    date = request.POST['date']

    allStations = request.POST.get('allStations', 0)

    sparkIp = getSparkIp()

    if str(allStations) == str(1):
        fileurl = request.POST['fileUrl']
        fileName = "measurement_" + str(date) + ".kmz"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/kmls")
        dirPath2 = os.path.join(dir1, fileName)

        try:
            response = requests.get(
                'http://' + sparkIp + ':5000/getAllStationsMeasurementsKML?date=' + date,
                stream=True)
        except requests.exceptions.ConnectionError:
            return render(request, '500.html')

        with open(dirPath2, 'wb') as f:
            logger.info("Downloading Cylinders KMZ from Flask...")
            for chunk in response.iter_content(chunk_size=1024):
                print('.', end='')
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
            f.close()

        sendKmlToLG(fileName, request)

        sendFlyToToLG("40.416775", "-3.703790", 25000, 0, 69, 130000, 2)

        playTour("Tour And Rotation")

        return render(request, 'floybd/weather/weatherConcreteView.html',
                      {'kml': fileurl, 'date': date})

    else:
        station_id = request.POST['station']
        weatherData = request.POST['weatherData']

    fileName = "measurement_" + str(date) + ".kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)

    response = requests.get('http://' + sparkIp + ':5000/getMeasurementKml?date='
                            + date + '&station_id=' + station_id, stream=True)
    with open(dirPath2, 'wb') as f:
        logger.info("Downloading Cylinders KMZ from Flask...")
        for chunk in response.iter_content(chunk_size=1024):
            print('.', end='')
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

    stations = Station.objects.all()
    concreteStation = Station.objects.get(station_id=station_id)

    sendKmlToLG(fileName, request)
    if concreteStation is not None:
        sendFlyToToLG(concreteStation.latitude, concreteStation.longitude, 25000, 0, 69, 130000, 2)

    playTour("Tour And Rotation")

    return render(request, 'floybd/weather/weatherConcreteView.html',
                  {'stations': stations, 'concreteStation': concreteStation,
                   'weatherData': weatherData, 'date': date})


def weatherConcreteIndex(request):
    stations = Station.objects.all()
    return render(request, 'floybd/weather/weatherConcrete.html', {'stations': stations})


def weatherPredictions(request):
    stations = Station.objects.all()
    columnsList = ["max_temp", "med_temp", "min_temp", "max_pressure", "min_pressure",
                   "precip", "insolation"]
    return render(request, 'floybd/weather/weatherPrediction.html',
                  {'stations': stations, 'columnsList': columnsList})


def getPrediction(request):
    station_id = request.POST['station']
    columnsToPredict = request.POST.getlist('columnToPredict')

    sparkIp = getSparkIp()
    ip = getDjangoIp()

    jsonData = {"station_id": station_id, "columnsToPredict": columnsToPredict}
    payload = json.dumps(jsonData)

    try:
        response = requests.post('http://' + sparkIp + ':5000/getPrediction',
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                                 data=payload)
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')

    if response.json():
        try:
            result = json.loads(response.json())
        except JSONDecodeError:
            return render(request, '500.html')
        concreteStation = Station.objects.get(station_id=station_id)

        kml = simplekml.Kml()
        tour = kml.newgxtour(name="Show Balloon")
        playlist = tour.newgxplaylist()

        contentString = '<link rel = "stylesheet" href = "https://code.getmdl.io/1.3.0/' \
                        'material.blue_grey-red.min.css" / > ' + \
                        '<link rel="stylesheet" href="https://fonts.googleapis.com/css?' \
                        'family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&lang=en"/>' + \
                        '<table width="470" style="font-family: Roboto;"><tr><td>' + \
                        '<div id="content">' + '<div id="siteNotice">' + '</div>' + \
                        '<h1 id="firstHeading" class="firstHeading" style="text-align:center">' + \
                        concreteStation.name + '</h1>' + \
                        '<div id="bodyContent" style="text-align: center;">' + \
                        '<div class="demo-charts mdl-color--white mdl-shadow--2dp mdl-cell' \
                        ' mdl-cell--6-col mdl-grid" style="width: 98%">'

        for row in result:
            jsonRow = json.loads(row)

            for column in columnsToPredict:
                if jsonRow.get("prediction_" + column) is not None:
                    contentString += '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' \
                                    '<p style="font-size:1.5em;color:#474747;">' \
                                     '<b>' + column + '</b>'\
                                     ':</p></div><div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' \
                                     '<p style="font-size:1.5em;color:#474747;">' + \
                                     str("%.2f" % round(jsonRow.get("prediction_" + column), 2)) + '</p></div>'
        contentString += '</div></div></div></td></tr></table>'

        point = kml.newpoint(name="", description=contentString,
                             coords=[(concreteStation.longitude, concreteStation.latitude)])
        point.style.iconstyle.icon.href = 'https://png.icons8.com/thermometer-automation/ultraviolet/80'
        point.style.balloonstyle.bgcolor = simplekml.Color.lightblue
        point.style.balloonstyle.text = "$[description]"
        point.gxballoonvisibility = 0

        doFlyToSmooth(playlist, concreteStation.latitude, concreteStation.longitude, 0, 4855570, 3.0, 0)
        playlist.newgxwait(gxduration=3.0)
        doFlyToSmooth(playlist, concreteStation.latitude, concreteStation.longitude, 1000, 5000, 5.0, 0)
        playlist.newgxwait(gxduration=5.0)
        doFlyToSmooth(playlist, concreteStation.latitude, concreteStation.longitude, 1000, 5000, 1)
        playlist.newgxwait(gxduration=1)

        animatedupdateshow = playlist.newgxanimatedupdate(gxduration=5.0)
        animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                           '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
            .format(point.placemark.id)

        doRotation(playlist, float(concreteStation.latitude), float(concreteStation.longitude), 1000, 5000)

        playlist.newgxwait(gxduration=5.0)

        animatedupdateshow = playlist.newgxanimatedupdate(gxduration=0.1)
        animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>0</visibility>' \
                                           '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
            .format(point.placemark.id)

        fileName = "prediction.kml"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/kmls")
        dirPath2 = os.path.join(dir1, fileName)

        kml.save(dirPath2)

        kmlpath = "http://" + ip + ":"+getDjangoPort(request)+"/static/kmls/" + fileName

        return render(request, 'floybd/weather/weatherPredictionView.html',
                      {'fileName': fileName, 'kml': kmlpath, 'backUrl': resolve("/predictWeather").url_name,
                       'concreteStation': concreteStation})
    else:
        return render(request, 'floybd/weather/weatherPredictionView.html')


def sendPredictionsToLG(request):
    fileName = request.POST.get("fileName")
    backUrl = request.POST.get("backUrl")
    ip = getDjangoIp()
    kmlpath = "http://" + ip + ":"+getDjangoPort(request)+"/static/kmls/" + fileName
    station_id = request.POST.get("station_id")
    stats = request.POST.get("stats", 0)

    concreteStation = Station.objects.get(station_id=station_id)

    sendKmlToLG(fileName, request)
    playTour("Show Balloon")

    return render(request, 'floybd/weather/weatherPredictionView.html',
                  {'fileName': fileName, 'kml': kmlpath, 'backUrl': backUrl,
                   'concreteStation': concreteStation, 'stats': stats == str("1")})


def weatherStats(request):
    stations = Station.objects.all()
    return render(request, 'floybd/weather/weatherStats.html', {'stations': stations})


def getStats(request):
    stations = Station.objects.all()

    ip = getDjangoIp()

    allStations = request.POST.get('allStations', 0)
    allStationsBool = allStations == str(1)
    allTime = request.POST.get('allTime', 0)
    dateFrom = request.POST.get('dateFrom', 0)
    dateTo = request.POST.get('dateTo', 0)
    station_id = request.POST.get('station', 0)
    addGraphs = request.POST.get('addGraphs', 0)

    addGraphs = (addGraphs == str("1"))

    logger.debug("AllStations:", allStations)
    logger.debug("allTime:", allTime)
    logger.debug("dateFrom:", dateFrom)
    logger.debug("dateTo:", dateTo)
    logger.debug("station_id:", station_id)
    logger.debug("addGraphs:", addGraphs)

    jsonData = {"station_id": station_id, "dateTo": dateTo, "dateFrom": dateFrom, "allTime": allTime,
                "allStations": allStations}

    payload = json.dumps(jsonData)

    try:
        response = requests.post('http://130.206.117.178:5000/getStats',
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                                 data=payload)
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')

    try:
        result = json.loads(response.json())
    except JSONDecodeError:
        return render(request, '500.html')
    intervalData = False
    oneStation = (allStations != str("1"))
    if allTime != str(1) and allStations != str(1):
        intervalData = True

    stationsWeather = {}
    kml = simplekml.Kml()

    if allStationsBool:
        tourAllStations = kml.newgxtour(name="Tour All Stations")
        playlistAllStations = tourAllStations.newgxplaylist()

    for row in result:
        concreteStation = Station.objects.get(station_id=row.get("station_id"))
        stationData = {}

        if allTime == str(1):
            if addGraphs:
                contentString = getContentStringWithGraphs(row)
            else:
                contentString = '<link rel = "stylesheet" href = "https://code.getmdl.io/1.3.0/' \
                                'material.blue_grey-red.min.css" / > ' + \
                                '<link rel="stylesheet" href="https://fonts.googleapis.com/css?' \
                                'family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&lang=en"/>' + \
                                '<table width="470" style="font-family: Roboto;"><tr><td>' + \
                                '<div id="content">' + '<div id="siteNotice">' + '</div>' + \
                                '<h1 id="firstHeading" class="firstHeading" style="text-align:center">' +\
                                concreteStation.name + '</h1>' + \
                                '<div id="bodyContent" style="text-align: center;">' + \
                                '<div class="demo-charts mdl-color--white mdl-shadow--2dp mdl-cell' \
                                ' mdl-cell--6-col mdl-grid" style="width: 98%">' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Average Max Temp:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str("%.2f" % round(row.get("avgMaxTemp"), 2)) + ' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Average Med Temp:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str("%.2f" % round(row.get("avgMedTemp"), 2)) + ' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Average Min Temp:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' + \
                                str("%.2f" % round(row.get("avgMinTemp"), 2))+' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Average Max Pressure :</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' + str(row.get("avgMaxPressure")) +\
                                ' hPa</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Average Min Pressure:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str(row.get("avgMinPressure")) + ' hPa</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Average Precipitation:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' + \
                                str("%.2f" % round(row.get("avgPrecip"), 2)) + ' mm</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Max Maximum Temperature:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str(row.get("maxMaxTemp")) + ' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Min Maximum Temperature:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str(row.get("minMaxTemp")) + ' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Max Medium Temperature:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str(row.get("maxMedTemp")) + ' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Min Medium Temperature:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str(row.get("minMedTemp")) + ' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Max Minimum Temperature:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str(row.get("maxMinTemp")) + ' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Min Minimum Temperature:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str(row.get("minMaxTemp")) + ' ºC</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">Max Precipitation:</p>' + \
                                '</div>' + \
                                '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                                '<p style="font-size:1.5em;color:#474747;">' +\
                                str(row.get("maxPrecip")) + ' mm</p>' + \
                                '</div>' + \
                                '</div>' + \
                                '</div></div>' + \
                                '</td></tr></table>'

        else:
            contentString = '<link rel = "stylesheet" href =' \
                            ' "https://code.getmdl.io/1.3.0/material.blue_grey-red.min.css" / > ' + \
                            '<link rel="stylesheet" href="https://fonts.googleapis.com/css?' \
                            'family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&lang=en"/>' + \
                            '<table width="470" style="font-family: Roboto;"><tr><td>' + \
                            '<div id="content">' + '<div id="siteNotice">' + '</div>' + \
                            '<h1 id="firstHeading" class="firstHeading" style="text-align:center">' +\
                            concreteStation.name + '</h1>' + \
                            '<div id="bodyContent" style="text-align: center;">' + \
                            '<div class="demo-charts mdl-color--white mdl-shadow--2dp mdl-cell' \
                            ' mdl-cell--6-col mdl-grid" style="width: 98%">' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Average Max Temp:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str("%.2f" % round(row.get("avg(max_temp)"), 2)) + ' ºC</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;"><b>Average Med Temp</b>:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + \
                            str("%.2f" % round(row.get("avg(med_temp)"), 2)) + ' ºC</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Average Min Temp:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + \
                            str("%.2f" % round(row.get("avg(min_temp)"), 2)) + ' ºC</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Average Max Pressure :</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str(row.get("avg(max_pressure)")) + ' hPa</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Average Min Pressure:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str(row.get("avg(min_pressure)")) + ' hPa</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Average Precipitation:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + \
                            str("%.2f" % round(row.get("avg(precip)"), 2)) + ' mm</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Insolation:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str(row.get("avg(insolation)")) + '</p>' + \
                            '</div>' + \
                            '</div>' + \
                            '</div></div>' + \
                            '</td></tr></table>'

        stationData["contentString"] = contentString
        stationData["latitude"] = concreteStation.latitude
        stationData["longitude"] = concreteStation.longitude
        stationData["name"] = concreteStation.name
        stationsWeather[row.get("station_id")] = stationData

        point = kml.newpoint(name=stationData["name"], description=stationData["contentString"],
                             coords=[(stationData["longitude"], stationData["latitude"])])
        point.style.iconstyle.icon.href = 'https://png.icons8.com/thermometer-automation/ultraviolet/80'
        point.style.balloonstyle.bgcolor = simplekml.Color.lightblue
        point.style.balloonstyle.text = "$[description]"
        # point.gxballoonvisibility = 0

        if allStationsBool:
            doFlyToSmooth(playlistAllStations,  float(stationData["latitude"]), float(stationData["longitude"]),
                          0, 4855570, 3.0, 0)
            playlistAllStations.newgxwait(gxduration=3.0)
            doFlyToSmooth(playlistAllStations,  float(stationData["latitude"]), float(stationData["longitude"]),
                          1000, 5000, 5.0, 0)
            playlistAllStations.newgxwait(gxduration=5.0)
            doFlyToSmooth(playlistAllStations,  float(stationData["latitude"]), float(stationData["longitude"]),
                          1000, 5000, 1)
            playlistAllStations.newgxwait(gxduration=1)

            animatedupdateshow = playlistAllStations.newgxanimatedupdate(gxduration=5.0)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                               '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)

            doRotation(playlistAllStations, float(stationData["latitude"]), float(stationData["longitude"]), 1000, 5000)

            playlistAllStations.newgxwait(gxduration=5.0)

            animatedupdateshow = playlistAllStations.newgxanimatedupdate(gxduration=0.1)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>0</visibility>' \
                                               '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)

        else:
            point.gxballoonvisibility = 0
            tour = kml.newgxtour(name="Show Balloon")
            playlist = tour.newgxplaylist()

            doFlyToSmooth(playlist, float(stationData["latitude"]), float(stationData["longitude"]), 0, 4855570, 3.0, 0)
            playlist.newgxwait(gxduration=3.0)
            doFlyToSmooth(playlist, float(stationData["latitude"]), float(stationData["longitude"]), 1000, 5000, 5.0, 0)
            playlist.newgxwait(gxduration=5.0)
            doFlyToSmooth(playlist, float(stationData["latitude"]), float(stationData["longitude"]), 1000, 5000, 1)
            playlist.newgxwait(gxduration=1)

            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=0.1)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                               '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)

            doRotation(playlist, float(stationData["latitude"]), float(stationData["longitude"]), 1000, 5000)

            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=0.1)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>0</visibility>' \
                                               '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)

    fileName = "stats.kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)
    concreteStation = Station.objects.get(station_id=station_id)

    kml.save(dirPath2)

    return render(request, 'floybd/weather/weatherStats.html', {'kml': 'http://' + ip + ':'+getDjangoPort(request) +
                                                                       '/static/kmls/' + fileName,
                                                                'stations': stations, 'fileName': fileName,
                                                                'intervalData': intervalData, "dateTo": dateTo,
                                                                "dateFrom": dateFrom, "station": station_id,
                                                                'concreteStation': concreteStation,
                                                                'oneStation': oneStation,
                                                                'allStations': allStations,
                                                                'allTime': allTime == str("1")})


def getContentStringWithGraphs(rowData):
    logger.info("Getting Graphs...")
    contentString = '<table width="600px"><tr><td class="balloonTd">' + \
                    '<center><h3><u>Max Temp</u></h3>' + \
                    '<br/><b>Avg Max Temp: </b>' + str("{0:.2f}".format(rowData.get("avgMaxTemp"))) + \
                    '<br/><b>Max Max Temp: </b>' + str("{0:.2f}".format(rowData.get("maxMaxTemp"))) + \
                    '<br/><b>Min Max Temp: </b>' + str("{0:.2f}".format(rowData.get("minMaxTemp"))) + \
                    '<br/><img width="100%" height="200px" src="http://130.206.117.178:5000/' \
                    'getStatsImage?station_id=' + rowData.get("station_id") + '&imageType=max_temp"/> ' + \
                    '</center></td><td class="balloonTd">' + \
                    '<center><h3><u>Med Temp</u></h3>' + \
                    '<br/><b>Avg Med Temp: </b>' + str("{0:.2f}".format(rowData.get("avgMedTemp"))) + \
                    '<br/><b>Max Med Temp: </b>' + str("{0:.2f}".format(rowData.get("maxMedTemp"))) + \
                    '<br/><b>Min Med Temp: </b>' + str("{0:.2f}".format(rowData.get("minMedTemp"))) + \
                    '<br/><img width="100%" height="200px" src="http://130.206.117.178:5000/' \
                    'getStatsImage?station_id=' + rowData.get("station_id") + '&imageType=med_temp"/> ' + \
                    '</center></td><td class="balloonTd">' + \
                    '<center><h3><u>Min Temp</u></h3>' + \
                    '<br/><b>Avg Min Temp: </b>' + str("{0:.2f}".format(rowData.get("avgMinTemp"))) + \
                    '<br/><b>Max Min Temp: </b>' + str("{0:.2f}".format(rowData.get("maxMinTemp"))) + \
                    '<br/><b>Min Min Temp: </b>' + str("{0:.2f}".format(rowData.get("minMinTemp"))) + \
                    '<br/><img width="100%" height="200px" src="http://130.206.117.178:5000/' \
                    'getStatsImage?station_id=' + rowData.get("station_id") + '&imageType=min_temp"/>' + \
                    '</center></td></tr><tr><td class="balloonTd">' + \
                    '<center><h3><u>Max Pressure</u></h3>' + \
                    '<br/><b>Avg Max Pressure: </b>' + str("{0:.2f}".format(rowData.get("avgMaxPressure"))) + \
                    '<br/><br/><img width="100%" height="200px" src="http://130.206.117.178:5000/' \
                    'getStatsImage?station_id=' + rowData.get("station_id") + '&imageType=max_pressure"/>' + \
                    '</center></td><td class="balloonTd">' + \
                    '<center><h3><u>Min Pressure</u></h3>' + \
                    '<br/><b>Avg Min Pressure: </b>' + str("{0:.2f}".format(rowData.get("avgMinPressure"))) + \
                    '<br/><br/><img width="100%" height="200px" src="http://130.206.117.178:5000/' \
                    'getStatsImage?station_id=' + rowData.get("station_id") + '&imageType=min_pressure"/> ' + \
                    '</center></td><td class="balloonTd">' + \
                    '<center><h3><u>Precipitation</u></h3>' + \
                    '<br/><b>Avg Precip: </b>' + str("{0:.2f}".format(rowData.get("avgPrecip"))) + \
                    '<br/><b>Max Precip: </b>' + str("{0:.2f}".format(rowData.get("maxPrecip"))) + \
                    '<br/><img width="100%" height="200px" src="http://130.206.117.178:5000/' \
                    'getStatsImage?station_id=' + rowData.get("station_id") + '&imageType=precip"/>' + \
                    '</center></td></tr></table>'

    return contentString


def getGraphDataForStats(request):
    station_id = request.GET.get("station")
    dateFrom = request.GET.get("dateFrom")
    dateTo = request.GET.get("dateTo")
    allTime = request.GET.get('allTime', 0)

    logger.debug("Station: ", station_id)
    logger.debug("Date From: ", dateFrom)
    logger.debug("Date To: ", dateTo)
    logger.debug("allTime: ", allTime)

    jsonData = {"station_id": station_id, "dateTo": dateTo, "dateFrom": dateFrom}
    payload = json.dumps(jsonData)

    try:
        response = requests.post('http://' + getSparkIp() + ':5000/getWeatherDataInterval',
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                                 data=payload)
        result = json.loads(response.json())
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')
    except JSONDecodeError:
        return render(request, '500.html')

    if result:
        data = {
            'stationData': result
        }
    else:
        data = {}

    return JsonResponse(data)


def sendStatsToLG(request):
    fileName = request.POST.get("fileName")
    sendKmlToLG(fileName, request)
    # sendKmlToLG1(fileName, request)
    stations = Station.objects.all()

    allStations = request.POST.get('allStations', 0)
    allTime = request.POST.get('allTime', 0)
    dateFrom = request.POST.get('dateFrom', 0)
    dateTo = request.POST.get('dateTo', 0)
    station_id = request.POST.get('station', 0)
    station = request.POST.get('station', 0)
    concreteStation = Station.objects.get(station_id=station)

    oneStation = (allStations != str("1"))
    intervalData = False
    if not allTime and not allStations:
        intervalData = True

    if oneStation:
        playTour("Show Balloon")

    else:
        sendFlyToToLG(40.4378693, -3.8199627, 1000, 0, 77, 5000, 2)
        time.sleep(2)
        playTour("Tour All Stations")

    ip = getDjangoIp()

    return render(request, 'floybd/weather/weatherStats.html', {'kml': 'http://' + ip + ':'+getDjangoPort(request) +
                                                                       '/static/kmls/' + fileName,
                                                                'stations': stations, 'fileName': fileName,
                                                                'intervalData': intervalData, "dateTo": dateTo,
                                                                "dateFrom": dateFrom, "station": station_id,
                                                                'concreteStation': concreteStation,
                                                                'oneStation': oneStation,
                                                                'allTime': allTime,
                                                                'allStations': allStations})


def citydashboard(request):
    stations = Station.objects.all()
    return render(request, 'floybd/weather/indexDashboard.html', {'stations': stations})


def viewDashboard(request):
    station = request.GET.get('station', None)
    daysBefore = request.GET.get('daysBefore', None)

    sparkIp = getSparkIp()

    today = time.strftime("%Y-%m-%d")
    previousDate = datetime.datetime.today() - timedelta(days=int(daysBefore))
    jsonData = {"station_id": station, "dateTo": today, "dateFrom": previousDate.strftime("%Y-%m-%d")}

    logger.debug("From: " + previousDate.strftime("%Y-%m-%d"))
    logger.debug("Today: " + today)

    payload = json.dumps(jsonData)

    try:
        response = requests.post('http://' + sparkIp + ':5000/getWeatherDataInterval',
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                                 data=payload)
        result = json.loads(response.json())
    except JSONDecodeError:
        return render(request, '500.html')
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')
    if result:
        data = {
            'stationData': result
        }
    else:
        data = {}
    return JsonResponse(data)


def weatherPredictionsStats(request):
    stations = Station.objects.all()

    return render(request, 'floybd/weather/weatherPredictionStats.html',
                  {'stations': stations})


def getPredictionStats(request):
    today = time.strftime("%Y-%m-%d")
    station_id = request.POST['station']
    sparkIp = getSparkIp()
    ip = getDjangoIp()

    jsonData = {"station_id": station_id, "fecha": today}
    payload = json.dumps(jsonData)

    try:
        response = requests.post('http://' + sparkIp + ':5000/getPredictionStats',
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                                 data=payload)
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')

    if response.json():
        try:
            result = json.loads(response.json())
        except JSONDecodeError:
            return render(request, '500.html')
        concreteStation = Station.objects.get(station_id=station_id)
        kml = simplekml.Kml()
        tour = kml.newgxtour(name="Show Balloon")
        playlist = tour.newgxplaylist()
        if len(result) > 0:

            contentString = '<link rel = "stylesheet" href =' \
                            ' "https://code.getmdl.io/1.3.0/material.blue_grey-red.min.css" / > ' + \
                            '<link rel="stylesheet" href="https://fonts.googleapis.com/css?' \
                            'family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&lang=en"/>' + \
                            '<table width="470" style="font-family: Roboto;"><tr><td>' + \
                            '<div id="content">' + '<div id="siteNotice">' + '</div>' + \
                            '<h1 id="firstHeading" class="firstHeading" style="text-align:center">' +\
                            concreteStation.name + '</h1>' + \
                            '<div id="bodyContent" style="text-align: center;">' + \
                            '<div class="demo-charts mdl-color--white mdl-shadow--2dp mdl-cell' \
                            ' mdl-cell--6-col mdl-grid" style="width: 98%">' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Max Temp:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str("%.2f" % round(result[0].get("max_temp"), 2)) + ' ºC</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Med Temp:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + \
                            str("%.2f" % round(result[0].get("med_temp"), 2)) + ' ºC</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Min Temp:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + \
                            str("%.2f" % round(result[0].get("min_temp"), 2)) + ' ºC</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Avg Precip:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' + \
                            str("%.2f" % round(result[0].get("precip"), 2)) + ' mm</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Max Press:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str("%.2f" % round(result[0].get("max_pressure"), 2)) + ' hPa</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Min Press:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str("%.2f" % round(result[0].get("min_pressure"), 2)) + ' hPa</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Insolation:</p>' + \
                            '</div>' + \
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str(result[0].get("insolation")) + '</p>' + \
                            '</div>' + \
                            '</div>' + \
                            '</div></div>' + \
                            '</td></tr></table>'

            point = kml.newpoint(name="", description=contentString, coords=[(concreteStation.longitude,
                                                                             concreteStation.latitude)])

            point.style.balloonstyle.bgcolor = simplekml.Color.lightblue
            point.style.balloonstyle.text = "$[description]"
            point.gxballoonvisibility = 0
            point.style.iconstyle.icon.href = 'https://png.icons8.com/thermometer-automation/ultraviolet/80'

            doFlyToSmooth(playlist, concreteStation.latitude, concreteStation.longitude, 0, 4855570, 3.0, 0)
            playlist.newgxwait(gxduration=3.0)
            doFlyToSmooth(playlist, concreteStation.latitude, concreteStation.longitude, 1000, 5000, 5.0, 0)
            playlist.newgxwait(gxduration=5.0)
            doFlyToSmooth(playlist, concreteStation.latitude, concreteStation.longitude, 1000, 5000, 1)
            playlist.newgxwait(gxduration=1)

            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=5.0)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                               '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)

            doRotation(playlist, float(concreteStation.latitude), float(concreteStation.longitude), 1000, 5000)

            playlist.newgxwait(gxduration=5.0)

            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=0.1)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>0</visibility>' \
                                               '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)

        fileName = "prediction.kml"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/kmls")
        dirPath2 = os.path.join(dir1, fileName)

        kml.save(dirPath2)

        kmlpath = "http://" + ip + ":"+getDjangoPort(request)+"/static/kmls/" + fileName

        return render(request, 'floybd/weather/weatherPredictionView.html',
                      {'fileName': fileName, 'kml': kmlpath, 'backUrl': resolve("/predictWeatherStats").url_name,
                       'concreteStation': concreteStation, 'stats': True})
    else:
        return render(request, 'floybd/weather/weatherPredictionView.html')


def currentWeather(request):
    logger.info("Getting current weather... ")
    try:
        response = requests.get('http://' + getSparkIp() + ':5000/getKey',
                                headers={'Accept': 'application/json', 'Content-Type': 'application/json'})

        api_key_resp = response.json()
        api_key = api_key_resp[0]['api_key']
    except requests.exceptions.ConnectionError:
        logger.error("Server not available. Getting local apiKey")
        apiKeyObject = ApiKey.objects.all()[0]
        api_key = apiKeyObject.key
        logger.info("Local ApiKey: ", api_key)

    querystring = {"api_key": api_key}
    headers = {'cache-control': "no-cache"}
    base_url = "https://opendata.aemet.es/opendata"

    currentWeatherData = getData(base_url + "/api/observacion/convencional/todas", headers, querystring)

    stationsDict = defaultdict(list)
    logger.info("Parsing current weather... ")
    kml = simplekml.Kml()
    tourCurrentWeather = kml.newgxtour(name="Tour Current Weather")
    playlistCurrentWeather = tourCurrentWeather.newgxplaylist()

    for row in currentWeatherData:
        jsonData = json.loads(json.dumps(row))
        stationId = jsonData.get("idema")
        stationsDict[stationId].append(jsonData)

    totalStations = len(stationsDict.items())
    stationNumber = 1

    logger.info("Generating current weather kml... ")
    for key, value in stationsDict.items():
        actualPercentage = (stationNumber/totalStations)*100
        printpercentage(actualPercentage)

        try:
            jsonData = json.loads(json.dumps(value[-1]))
        except JSONDecodeError:
            return render(request, '500.html')

        latitude = float(jsonData.get("lat"))
        longitude = float(jsonData.get("lon"))
        datetimeStr = datetime.datetime.strptime(jsonData.get("fint"), "%Y-%m-%dT%H:%M:%S").strftime(
            '%H:%M:%S %Y-%m-%d')

        contentString = '<link rel = "stylesheet" href = "' \
                        'https://code.getmdl.io/1.3.0/material.blue_grey-red.min.css" / > ' + \
                        '<link rel="stylesheet" href="https://fonts.googleapis.com/css?' \
                        'family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&lang=en"/>' + \
                        '<table width="470" style="font-family: Roboto;"><tr><td>' + \
                        '<div id="content">' + '<div id="siteNotice">' + '</div>' + \
                        '<h1 id="firstHeading" class="firstHeading" style="text-align:center">' +\
                        jsonData.get("ubi") + '</h1>' + \
                        '<h2 id="firstHeading" class="secondHeading" style="text-align:center">Station ID: ' +\
                        jsonData.get("idema") + '</h2>' + \
                        '<h3 id="firstHeading" class="thirdHeading" style="text-align:center">Date: ' +\
                        datetimeStr + '</h3>' + \
                        '<div id="bodyContent" style="text-align: center;">' + \
                        '<div class="demo-charts mdl-color--white mdl-shadow--2dp' \
                        ' mdl-cell mdl-cell--6-col mdl-grid" style="width: 98%">' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Max Temp:</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                        str(jsonData.get("tamax")) + ' ºC</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;"><b>Actual Temp</b>:</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                        str(jsonData.get("ta")) + ' ºC</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Min Temp:</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                        str(jsonData.get("tamin")) + ' ºC</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Relative Humidity :</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                        str(jsonData.get("hr")) + ' %</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Precipitation:</p>' + \
                        '</div>' + \
                        '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' + \
                        '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                        str(jsonData.get("precip")).replace("None", "0") + ' mm</p>' + \
                        '</div>' + \
                        '</div>' + \
                        '</div></div>' + \
                        '</td></tr></table>'

        point = kml.newpoint(name=jsonData.get("ubi"), description=contentString,
                             coords=[(longitude, latitude)])

        point.style.balloonstyle.bgcolor = simplekml.Color.lightblue
        point.style.balloonstyle.text = contentString
        point.style.iconstyle.icon.href = 'https://png.icons8.com/thermometer-automation/ultraviolet/80'
        point.gxballoonvisibility = 0

        doFlyTo(playlistCurrentWeather, latitude, longitude, 1000, 5000, 3.0)
        playlistCurrentWeather.newgxwait(gxduration=3.0)

        animatedupdateshow = playlistCurrentWeather.newgxanimatedupdate(gxduration=5.0)
        animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                           '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
            .format(point.placemark.id)

        doRotation(playlistCurrentWeather, latitude, longitude, 1000, 5000)

        animatedupdateshow = playlistCurrentWeather.newgxanimatedupdate(gxduration=0.1)
        animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>0</visibility>' \
                                           '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
            .format(point.placemark.id)

        stationNumber += 1

    fileName = "currentWeather.kmz"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)

    kml.savekmz(dirPath2, format=False)
    command = "echo '' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    sendKmlToLG(fileName, request)
    time.sleep(5)
    playTour("Tour Current Weather")

    return HttpResponse(status=204)


def getData(url, headers, querystring):
    """	Make the request to the api	"""
    try:
        response = requests.request("GET", url, headers=headers, params=querystring, verify=False)

        if response:
            jsonResponse = response.json()
            if jsonResponse.get('estado') == 200:
                link = jsonResponse.get('datos')
                data = requests.request("GET", link, verify=False)
                if data.status_code == 200:
                    return data.json()
                else:
                    return 0
            elif jsonResponse.get('estado') == 429:
                # Sleep until next minute
                logger.debug("####Sleeping")
                time.sleep(60)
                logger.debug("####Waked up!!")
                return getData(url)
    except requests.exceptions.ConnectionError:
        logger.error("####ERROR!! => Sleeping")
        time.sleep(120)
        logger.debug("####Waked up!!")
        return getData(url)


def dummyWeather(request):

    sendDemoKmlToLG("dummyWeather.kmz", request)
    time.sleep(3)
    playTour("Tour Current Weather")

    return HttpResponse(status=204)
