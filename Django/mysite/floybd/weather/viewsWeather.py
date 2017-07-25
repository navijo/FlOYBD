from django.shortcuts import render
from ..models import Station
from ..models import ApiKey
import requests
import json
import time
import datetime
from datetime import timedelta
from ..utils.lgUtils import *
from django.http import JsonResponse, HttpResponse
from collections import defaultdict


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def getConcreteValues(request):
    date = request.POST['date']
    station_id = request.POST.get('station', 0)
    allStations = request.POST.get('allStations', 0)

    sparkIp = getSparkIp()
    ip = getDjangoIp()

    getAllStations = allStations == str(1)

    stations = Station.objects.all()

    try:
        response = requests.get(
            'http://' + sparkIp + ':5000/getMeasurement?date=' + date + '&station_id=' + station_id + '&allStations=' + str(
                getAllStations), stream=True)
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')

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

        millis = int(round(time.time() * 1000))
        fileName = "measurement_" + str(date) + "_" + str(millis) + ".kml"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/kmls")
        dirPath2 = os.path.join(dir1, fileName)

        kml.save(dirPath2)
        return render(request, 'floybd/weather/weatherConcreteView.html',
                      {'kml': 'http://' + ip + ':8000/static/kmls/' + fileName, 'date': date})
    else:
        concreteStation = Station.objects.get(station_id=station_id)
        contentString = stationsWeather[station_id]["contentString"]
        return render(request, 'floybd/weather/weatherConcreteView.html',
                      {'stations': stations, 'concreteStation': concreteStation,
                       'weatherData': contentString, 'date': date})


def sendConcreteValuesToLG(request):
    date = request.POST['date']
    millis = int(round(time.time() * 1000))

    allStations = request.POST.get('allStations', 0)

    sparkIp = getSparkIp()

    if str(allStations) == str(1):
        fileurl = request.POST['fileUrl']
        millis = int(round(time.time() * 1000))

        fileName = "measurement_" + str(date) + "_" + str(millis) + ".kmz"
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
            print("Downloading Cylinders KMZ from Flask...")
            for chunk in response.iter_content(chunk_size=1024):
                print('.', end='')
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
            f.close()

        sendKmlToLG(fileName)

        sendFlyToToLG("40.416775", "-3.703790", 25000, 0, 69, 130000, 2)

        playTour("Tour And Rotation")

        return render(request, 'floybd/weather/weatherConcreteView.html',
                      {'kml': fileurl, 'date': date})

    else:
        station_id = request.POST['station']
        weatherData = request.POST['weatherData']

    fileName = "measurement_" + str(date) + "_" + str(millis) + ".kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)

    response = requests.get('http://' + sparkIp + ':5000/getMeasurementKml?date='
                            + date + '&station_id=' + station_id, stream=True)
    with open(dirPath2, 'wb') as f:
        print("Downloading Cylinders KMZ from Flask...")
        for chunk in response.iter_content(chunk_size=1024):
            print('.', end='')
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

    stations = Station.objects.all()
    concreteStation = Station.objects.get(station_id=station_id)

    sendKmlToLG(fileName)
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
        result = json.loads(response.json())
        concreteStation = Station.objects.get(station_id=station_id)
        predictionStr = ""
        kml = simplekml.Kml()
        for row in result:
            jsonRow = json.loads(row)

            for column in columnsToPredict:
                if jsonRow.get("prediction_" + column) is not None:
                    predictionStr += '<br/><b>' + column + ': </b>' + str(jsonRow.get("prediction_" + column))

        contentString = '<div id="content">' + \
                        '<div id="siteNotice">' + \
                        '</div>' + \
                        '<div id="bodyContent">' + \
                        '<p>' + predictionStr + '</p>' + \
                        '</div>' + \
                        '</div>'
        kml.newpoint(name=concreteStation.name, description=contentString,
                     coords=[(concreteStation.longitude, concreteStation.latitude)])

        millis = int(round(time.time() * 1000))
        fileName = "prediction_" + str(millis) + ".kml"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/kmls")
        dirPath2 = os.path.join(dir1, fileName)

        kml.save(dirPath2)

        kmlpath = "http://" + ip + ":8000/static/kmls/" + fileName

        return render(request, 'floybd/weather/weatherPredictionView.html',
                      {'fileName': fileName, 'kml': kmlpath,
                       'concreteStation': concreteStation})
    else:
        return render(request, 'floybd/weather/weatherPredictionView.html')


def sendPredictionsToLG(request):
    fileName = request.POST.get("fileName")
    ip = getDjangoIp()
    kmlpath = "http://" + ip + ":8000/static/kmls/" + fileName

    station_id = request.POST.get("station_id")
    stats = request.POST.get("stats", 0)

    concreteStation = Station.objects.get(station_id=station_id)

    sendKmlToLG(fileName)
    if concreteStation is not None:
        sendFlyToToLG(concreteStation.latitude, concreteStation.longitude, 100, 14, 69, 200000, 2)

    time.sleep(1)
    playTour("Show Balloon")

    return render(request, 'floybd/weather/weatherPredictionView.html',
                  {'fileName': fileName, 'kml': kmlpath,
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

    print("AllStations:", allStations)
    print("allTime:", allTime)
    print("dateFrom:", dateFrom)
    print("dateTo:", dateTo)
    print("station_id:", station_id)
    print("addGraphs:", addGraphs)

    jsonData = {"station_id": station_id, "dateTo": dateTo, "dateFrom": dateFrom, "allTime": allTime,
                "allStations": allStations}

    payload = json.dumps(jsonData)

    try:
        response = requests.post('http://130.206.117.178:5000/getStats',
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                                 data=payload)
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')

    result = json.loads(response.json())
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
                contentString = '<div id="content">' + \
                                '<div id="siteNotice">' + \
                                '</div>' + \
                                '<h1 id="firstHeading" class="firstHeading">' + concreteStation.name + '</h1>' + \
                                '<div id="bodyContent">' + \
                                '<br/><b>Avg Max Temp: </b>' + str(row.get("avgMaxTemp")) + \
                                '<br/><b>Avg Med Temp: </b>' + str(row.get("avgMedTemp")) + \
                                '<br/><b>Avg Min Temp: </b>' + str(row.get("avgMinTemp")) + \
                                '<br/><b>Avg Max Pressure: </b>' + str(row.get("avgMaxPressure")) + \
                                '<br/><b>Avg Min Pressure: </b>' + str(row.get("min_pressure")) + \
                                '<br/><b>Avg Precip: </b>' + str(row.get("avgPrecip")) + \
                                '<br/><b>Max Max Temp: </b>' + str(row.get("maxMaxTemp")) + \
                                '<br/><b>Min Max Temp: </b>' + str(row.get("minMaxTemp")) + \
                                '<br/><b>Max Med Temp: </b>' + str(row.get("maxMedTemp")) + \
                                '<br/><b>Min Med Temp: </b>' + str(row.get("minMedTemp")) + \
                                '<br/><b>Max Min Temp: </b>' + str(row.get("maxMinTemp")) + \
                                '<br/><b>Min Min Temp: </b>' + str(row.get("minMinTemp")) + \
                                '<br/><b>Max Precip: </b>' + str(row.get("maxPrecip")) + \
                                '</div>' + \
                                '</div>'
        else:
            contentString = '<div id="content">' + \
                            '<div id="siteNotice">' + \
                            '</div>' + \
                            '<h1 id="firstheading" class="firstheading">' + concreteStation.name + '</h1>' + \
                            '<div id="bodycontent">' + \
                            '<p>' + \
                            '<br/><b>Avg max temp: </b>' + str(row.get("avg(max_temp)")) + \
                            '<br/><b>Avg med temp: </b>' + str(row.get("avg(med_temp)")) + \
                            '<br/><b>Avg min temp: </b>' + str(row.get("avg(min_temp)")) + \
                            '<br/><b>Avg max pressure: </b>' + str(row.get("avg(max_pressure)")) + \
                            '<br/><b>Avg min pressure: </b>' + str(row.get("avg(min_pressure)")) + \
                            '<br/><b>Avg Precip: </b>' + str(row.get("avg(precip)")) + \
                            '<br/><b>Avg insolation: </b>' + str(row.get("avg(insolation)")) + \
                            '</p>' + \
                            '</div>' + \
                            '</div>'

        stationData["contentString"] = contentString
        stationData["latitude"] = concreteStation.latitude
        stationData["longitude"] = concreteStation.longitude
        stationData["name"] = concreteStation.name
        stationsWeather[row.get("station_id")] = stationData

        point = kml.newpoint(name=stationData["name"], description=stationData["contentString"],
                     coords=[(stationData["longitude"], stationData["latitude"])])

        point.style.balloonstyle.bgcolor = simplekml.Color.lightblue
        point.style.balloonstyle.text = stationData["contentString"]
        #point.gxballoonvisibility = 0

        if allStationsBool:
            flyto = playlistAllStations.newgxflyto(gxduration=5.0)
            flyto.camera.longitude = float(stationData["longitude"])
            flyto.camera.latitude = float(stationData["latitude"])
            flyto.camera.altitude = 5000
            flyto.camera.heading = 100
            flyto.camera.tilt = 14
            flyto.camera.roll = 0

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


            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=0.1)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                           '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)

            doRotation(playlist, float(stationData["latitude"]), float(stationData["longitude"]), 1000, 5000)

            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=0.1)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>0</visibility>' \
                                               '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)


    millis = int(round(time.time() * 1000))
    fileName = "stats_" + str(millis) + ".kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)
    concreteStation = Station.objects.get(station_id=station_id)

    kml.save(dirPath2)

    return render(request, 'floybd/weather/weatherStats.html', {'kml': 'http://' + ip + ':8000/static/kmls/' + fileName,
                                                                'stations': stations, 'fileName': fileName,
                                                                'intervalData': intervalData, "dateTo": dateTo,
                                                                "dateFrom": dateFrom, "station": station_id,
                                                                'concreteStation': concreteStation,
                                                                'oneStation': oneStation,
                                                                'allStations': allStations,
                                                                'allTime': allTime == str("1")})


def getContentStringWithGraphs(rowData):
    print("Getting Graphs...")
    contentString = '<table width="600px"><tr><td class="balloonTd">'+\
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

    print("Station: ", station_id)
    print("Date From: ", dateFrom)
    print("Date To: ", dateTo)
    print("allTime: ", allTime)

    jsonData = {"station_id": station_id, "dateTo": dateTo, "dateFrom": dateFrom}
    payload = json.dumps(jsonData)

    try:
        response = requests.post('http://' + getSparkIp() + ':5000/getWeatherDataInterval',
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                                 data=payload)
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')

    result = json.loads(response.json())
    if result:
        data = {
            'stationData': result
        }
    else:
        data = {}

    return JsonResponse(data)


def sendStatsToLG(request):
    fileName = request.POST.get("fileName")
    sendKmlToLG(fileName)
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
        sendFlyToToLG(concreteStation.latitude, concreteStation.longitude, 1000, 0, 77, 5000, 2)

        time.sleep(7)
        playTour("Show Balloon")

    else:
        sendFlyToToLG(40.4378693, -3.8199627, 1000, 0, 77, 5000, 2)
        time.sleep(2)
        playTour("Tour All Stations")

    ip = getDjangoIp()

    return render(request, 'floybd/weather/weatherStats.html', {'kml': 'http://' + ip + ':8000/static/kmls/' + fileName,
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

    print("From: " + previousDate.strftime("%Y-%m-%d"))
    print("Today: " + today)

    payload = json.dumps(jsonData)

    try:
        response = requests.post('http://' + sparkIp + ':5000/getWeatherDataInterval',
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                                 data=payload)
    except requests.exceptions.ConnectionError:
        return render(request, '500.html')

    result = json.loads(response.json())
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
        result = json.loads(response.json())
        concreteStation = Station.objects.get(station_id=station_id)
        kml = simplekml.Kml()
        if len(result) > 0:
            contentString = '<div id="content">' + \
                            '<div id="siteNotice">' + \
                            '</div>' + \
                            '<h3 id="firstheading" class="firstheading">' + concreteStation.province + '</h3>' + \
                            '<div id="bodycontent">' + \
                            '<p>' + \
                            '<br/><b>Max temp: </b>' + str(result[0].get("max_temp")) + \
                            '<br/><b>Med temp: </b>' + str(result[0].get("med_temp")) + \
                            '<br/><b>Min temp: </b>' + str(result[0].get("min_temp")) + \
                            '<br/><b>Max pressure: </b>' + str(result[0].get("max_pressure")) + \
                            '<br/><b>Min pressure: </b>' + str(result[0].get("min_pressure")) + \
                            '<br/><b>Precip: </b>' + str(result[0].get("precip")) + \
                            '<br/><b>Insolation: </b>' + str(result[0].get("insolation")) + \
                            '</p>' + \
                            '</div>' + \
                            '</div>'

            point = kml.newpoint(name=concreteStation.name, description=contentString,
                         coords=[(concreteStation.longitude, concreteStation.latitude)])

            point.style.balloonstyle.bgcolor = simplekml.Color.lightblue
            point.gxballoonvisibility = 0

            tour = kml.newgxtour(name="Show Balloon")
            playlist = tour.newgxplaylist()

            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=0.1)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                               '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
                .format(point.placemark.id)

        millis = int(round(time.time() * 1000))
        fileName = "prediction_" + str(millis) + ".kml"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/kmls")
        dirPath2 = os.path.join(dir1, fileName)

        kml.save(dirPath2)

        kmlpath = "http://" + ip + ":8000/static/kmls/" + fileName

        return render(request, 'floybd/weather/weatherPredictionView.html',
                      {'fileName': fileName, 'kml': kmlpath,
                       'concreteStation': concreteStation, 'stats': True})
    else:
        return render(request, 'floybd/weather/weatherPredictionView.html')


def currentWeather(request):
    print("Getting current weather... ")
    try:
        response = requests.get('http://' + getSparkIp() + ':5000/getKey',
                                headers={'Accept': 'application/json', 'Content-Type': 'application/json'})

        api_key_resp = response.json()
        api_key = api_key_resp[0]['api_key']
    except requests.exceptions.ConnectionError:
        print("Server not available. Getting local apiKey")
        apiKeyObject = ApiKey.objects.all()[0]
        api_key = apiKeyObject.key
        print("Local ApiKey: ", api_key)

    querystring = {"api_key": api_key}
    headers = {'cache-control': "no-cache"}
    base_url = "https://opendata.aemet.es/opendata"

    currentWeatherData = getData(base_url + "/api/observacion/convencional/todas", headers, querystring)

    stationsDict = defaultdict(list)
    print("Parsing current weather... ")
    kml = simplekml.Kml()
    tourCurrentWeather = kml.newgxtour(name="Tour Current Weather")
    playlistCurrentWeather = tourCurrentWeather.newgxplaylist()

    for row in currentWeatherData:
        jsonData = json.loads(json.dumps(row))
        stationId = jsonData.get("idema")
        stationsDict[stationId].append(jsonData)

    totalStations = len(stationsDict.items())
    stationNumber = 1

    print("Generating current weather kml... ")
    for key, value in stationsDict.items():
        actualPercentage = (stationNumber/totalStations)*100
        printpercentage(actualPercentage)
        jsonData = json.loads(json.dumps(value[-1]))
        latitude = float(jsonData.get("lat"))
        longitude = float(jsonData.get("lon"))
        altitude = float(jsonData.get("alt"))

        contentString = '<div id="content">' + \
                        '<div id="siteNotice">' + \
                        '</div>' + \
                        '<h1 id="firstheading" class="firstheading">' + jsonData.get("ubi")+'</h1>' + \
                        '<h2 id="secondheading" class="secondheading">' + jsonData.get("idema") + '</h2>' + \
                        '<h3 id="thirdheading" class="thirdheading">' + jsonData.get("fint") + '</h3>' + \
                        '<div id="bodycontent">' + \
                        '<p>' + \
                        '<br/><b>Max Temp: </b>' + str(jsonData.get("tamax")) + \
                        '<br/><b>Actual Temp: </b>' + str(jsonData.get("ta")) + \
                        '<br/><b>Min temp: </b>' + str(jsonData.get("tamin")) + \
                        '<br/><b>Relative Humidity: </b>' + str(jsonData.get("hr")) + \
                        '<br/><b>Precip: </b>' + str(jsonData.get("prec")) + \
                        '</p>' + \
                        '</div>' + \
                        '</div>'

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

    millis = int(round(time.time() * 1000))
    fileName = "currentWeather" + str(millis) + ".kmz"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/kmls")
    dirPath2 = os.path.join(dir1, fileName)

    kml.savekmz(dirPath2, format=False)
    command = "echo '' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    sendKmlToLG(fileName)
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
                print("####Sleeping")
                time.sleep(60)
                print("####Waked up!!")
                return getData(url)
    except requests.exceptions.ConnectionError:
        print("####ERROR!! => Sleeping")
        time.sleep(120)
        print("####Waked up!!")
        return getData(url)


def dummyWeather(request):
    '''stopTour()

    command = "echo '' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)'''

    sendDemoKmlToLG("dummyWeather.kmz")
    time.sleep(3)
    playTour("Tour Current Weather")

    return HttpResponse(status=204)

