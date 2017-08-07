from django.shortcuts import render

from ..utils.gtfsUtils import *

from ..forms import UploadFileForm
from ..gtfs_models import Agency
from ..utils.lgUtils import *
from django.http import HttpResponse


import tarfile
import time
import zipfile
import simplekml
import random

import logging
logger = logging.getLogger("django")


def uploadGTFS(request):
    if request.method == 'POST':
        title = request.POST['title']
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            millis = int(round(time.time() * 1000))
            form.title = title
            handle_uploaded_file(request.FILES['file'], form.title, millis)

            agencies = Agency.objects.all()
            return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})
    else:
        form = UploadFileForm()
        return render(request, 'floybd/indexGTFS.html', {'form': form})


def handle_uploaded_file(f, title, millis):
    if not os.path.exists("static/upload/gtfs"):
        logger.info("Creating upload/gtfs folder")
        os.makedirs("static/upload/gtfs")

    extension = get_extension(f)
    logger.info("Extension:" + str(extension))
    if extension not in [".zip", ".tar", ".tgz"]:
        logger.info("Saving normal File")
        saveNormalFile(f, title, extension)
    else:
        saveNormalFile(f, title, extension)
        decompressFile(f, title, extension)
        parseGTFS(title)


def parseGTFS(title):
    parseAgency("static/upload/gtfs/" + title)
    parseCalendar("static/upload/gtfs/" + title)
    parseCalendarDates("static/upload/gtfs/" + title)
    parseStops("static/upload/gtfs/" + title)
    parseRoutes("static/upload/gtfs/" + title)
    parseTrips("static/upload/gtfs/" + title)
    parseStopTimes("static/upload/gtfs/" + title)


def get_extension(file):
    name, extension = os.path.splitext(file.name)
    return extension


def saveNormalFile(file, title, extension):
    with open('static/upload/gtfs/' + title + extension, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def decompressFile(file, title, extension):
    logger.info("Decompressing..." + extension)
    if str(extension) == str('.zip'):
        logger.info("Is Zip")
        opener, mode = zipfile.ZipFile, 'r'
    elif str(extension) == str('.tar.gz') or str(extension) == str('.tgz'):
        logger.info("Is GZ")
        opener, mode = tarfile.open, 'r:gz'
    elif str(extension) == str('.tar.bz2') or str(extension) == str('.tbz'):
        logger.info("Is Tar")
        opener, mode = tarfile.open, 'r:bz2'
    else:
        raise (ValueError, "Could not extract `%s` as no appropriate extractor is found" % file)

    cwd = os.getcwd()

    if not os.path.exists("static/upload/gtfs/" + title):
        os.makedirs("static/upload/gtfs/" + title)

    os.chdir("static/upload/gtfs/" + title)

    try:
        compressedFile = opener(file, mode)
        try:
            compressedFile.extractall()
        finally:
            compressedFile.close()
    finally:
        os.chdir(cwd)


def sendGTFSToLG(request):
    kmlName = request.POST["kmlName"]
    kmlPath = request.POST["kmlPath"]
    carKml = request.POST["carKml"]
    flyToLat = request.POST["flyToLat"]
    flyToLon = request.POST["flyToLon"]
    lgIp = getLGIp()
    ip = getDjangoIp()

    command = "echo 'http://" + ip + ":"+getDjangoPort(request)+"/static/kmls/" + kmlName + \
              "\nhttp://" + ip + ":"+getDjangoPort(request)+"/static/kmls/" + carKml + \
              "' | sshpass -p lqgalaxy ssh lg@" + lgIp + " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    sendFlyToToLG(flyToLat, flyToLon, 6000000, 0, 0, 1, 4)

    time.sleep(5)
    playTour("GTFSTour")

    return render(request, 'floybd/gtfs/viewGTFS.html', {'kml': 'http://' + ip + ':'+getDjangoPort(request) +
                                                                '/static/kmls/' + kmlName,
                                                         'flyToLon': flyToLon, 'flyToLat': flyToLat,
                                                         'carKml': carKml, 'kmlName': kmlName})


def uploadgtfs(request):
    logger.info("Upload GTFS")
    form = UploadFileForm()
    return render(request, 'floybd/gtfs/gtfsUpload.html', {'form': form})


def viewgtfs(request):
    logger.info("View GTFS")
    agencies = Agency.objects.all()
    return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})


def getAgenciesAndGenerateKML(request):
    agencies = request.POST.getlist('agenciesSelected')
    maxCars = int(request.POST.get('maxCars'))
    stops_added = []
    tripsAdded = []

    millis = int(round(time.time() * 1000))

    carsCounter = 0
    kmlCars = simplekml.Kml()
    kmlLines = simplekml.Kml()
    tourCars = kmlCars.newgxtour(name="GTFSTour")
    playlistCars = tourCars.newgxplaylist()
    folderCars = kmlCars.newfolder(name="Cars")
    folderCars.visibility = 1

    firstPlacemark = True
    addedStops = []
    addedLines = {}

    for selectedAgency in agencies:
        agency = Agency.objects.get(agency_id=selectedAgency)
        logger.info("Agency Name : " + str(agency.agency_name))
        routes = Route.objects.filter(agency=agency)
        for route in routes:
            logger.info("Route Name : " + str(route.route_long_name))
            trips = Trip.objects.filter(route_id=route.route_id)

            for trip in trips:
                if trip.trip_id not in tripsAdded:
                    tripsAdded.append(trip)
                    logger.info("Trip Id : " + str(trip.trip_id))
                    stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
                    for index, current in enumerate(stop_times):
                        if index + 1 >= len(stop_times):
                            continue
                        nextelem = stop_times[index + 1]

                        stop1 = current.stop
                        stop2 = nextelem.stop
                        if stop1 not in addedStops:
                            addedStops.append(stop1)
                            doPlacemarks(stop1, kmlLines)
                        if stop2 not in addedStops:
                            addedStops.append(stop2)
                            doPlacemarks(stop2, kmlLines)


    ip = getDjangoIp()

    flyToLatMax = 0
    flyToLatMin = 0
    flyToLonMax = 0
    flyToLonMin = 0

    createCars(maxCars, tripsAdded, folderCars, playlistCars, kmlLines)

    for trip in tripsAdded:
        stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
        for index, current in enumerate(stop_times):
            if index + 1 >= len(stop_times):
                continue
            nextelem = stop_times[index + 1]

            stop1 = current.stop
            stop2 = nextelem.stop
            key = (stop1.stop_id, stop2.stop_id)

            if flyToLatMax == 0:
                flyToLatMax = stop1.stop_lat
                flyToLatMin = stop1.stop_lat
            elif stop1.stop_lat > flyToLatMax:
                flyToLatMax = stop1.stop_lat
            elif stop1.stop_lat < flyToLatMin:
                flyToLatMin = stop1.stop_lat

            if flyToLonMax == 0:
                flyToLonMax = stop1.stop_lon
                flyToLonMin = stop1.stop_lon
            elif stop1.stop_lon > flyToLonMax:
                flyToLonMax = stop1.stop_lon
            elif stop1.stop_lon < flyToLonMin:
                flyToLonMin = stop1.stop_lon

            if key not in addedLines:
                logger.info("\t Adding not included line")
                doLinesNotIncluded(stop1, stop2, kmlLines)

    flyToLon = (flyToLonMax + flyToLonMin) / 2
    flyToLat = (flyToLatMax + flyToLatMin) / 2

    carKml = "car_" + str(millis) + ".kmz"
    linesKml = "lines_" + str(millis) + ".kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/img")
    imagePath = os.path.join(dir1, "trainYellow.png")
    imagePath2 = os.path.join(dir1, "trainBlue.png")
    logger.debug("Image located in " + imagePath)
    logger.info("Cars to be added: " + str(maxCars))

    kmlCars.addfile(imagePath)
    kmlCars.addfile(imagePath2)
    kmlCars.savekmz("static/kmls/" + carKml, format=False)
    kmlLines.save("static/kmls/" + linesKml)

    return render(request, 'floybd/gtfs/viewGTFS.html', {'kml': 'http://' + ip + ':'+getDjangoPort(request) +
                                                                '/static/kmls/' + linesKml,
                                                         'flyToLon': flyToLon, 'flyToLat': flyToLat,
                                                         'carKml': carKml, 'kmlName': linesKml})


def createCars(maxCars, trips, folderCars, playlistCars, kmlLines):
    carsCounter = 0

    firstPlacemark = True
    addedLines = {}

    while carsCounter < maxCars:
        #We take a random trip
        randomTrip = random.sample(trips, 1)
        #We get its stops
        stop_times = Stop_time.objects.filter(trip_id=randomTrip[0].trip_id)
        logger.info("\tNew Car #" + str(carsCounter))

        for index, current in enumerate(stop_times):
            if index + 1 >= len(stop_times):
                continue
            nextelem = stop_times[index + 1]

            stop1 = current.stop
            stop2 = nextelem.stop

            if len(stop_times) > 2:
                '''Trip with more than 2 stops. We get from origin to final destiny'''
                stopSrc = stop_times[0].stop
                stopDst = stop_times[len(stop_times) - 1].stop
                routeName = 'From ' + str(stopSrc.stop_name) + ' to ' + str(stopDst.stop_name)
                logger.info("\t Found long trip with " + str(len(stop_times)) + " stops. From " + stopSrc.stop_name
                            + " to " + stopDst.stop_name)
                isLongTrip = True
            else:
                routeName = 'From ' + str(stop1.stop_name) + ' to ' + str(stop2.stop_name)
                isLongTrip = False

            doCarsMovement(stop1, stop2, folderCars, playlistCars, firstPlacemark, kmlLines, addedLines, routeName,
                           isLongTrip)

            if firstPlacemark:
                firstPlacemark = False
        carsCounter += 1

    logger.info("Cars really added: " + str(carsCounter))

    return


def doPlacemarks(stop, kmlTrips):
    point = kmlTrips.newpoint(name=stop.stop_name + " HUB")
    point.coords = [(stop.stop_lon, stop.stop_lat, 50000)]
    point.altitudemode = simplekml.AltitudeMode.relativetoground
    point.extrude = 1
    point.linestyle.width = 20
    point.style.labelstyle.scale = 1.5
    point.style.labelstyle.color = simplekml.Color.blue
    point.style.linestyle.color = simplekml.Color.blue
    point.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/shapes/subway.png"


def doLinesNotIncluded(stopSrc, stopDst, kmlTrips):

    linestring = kmlTrips.newlinestring(name='From '+str(stopSrc.stop_name)+' to '+str(stopDst.stop_name))
    linestring.coords = [(stopSrc.stop_lon, stopSrc.stop_lat, 50000), (stopDst.stop_lon, stopDst.stop_lat, 50000)]
    linestring.altitudemode = simplekml.AltitudeMode.relativetoground
    #linestring.extrude = 1
    linestring.tesellate = 1
    linestring.style.linestyle.width = 15
    linestring.style.linestyle.color = "FF7800F0"


def doLines(stopSrc, stopDst, startLat, startLon, dstLat, dstLon, kmlTrips):

    linestring = kmlTrips.newlinestring(name='From '+str(stopSrc.stop_name)+' to '+str(stopDst.stop_name))
    linestring.coords = [(startLon, startLat, 50000), (dstLon, dstLat, 50000)]
    linestring.altitudemode = simplekml.AltitudeMode.relativetoground
    #linestring.extrude = 1
    linestring.tesellate = 1
    linestring.style.linestyle.width = 15
    linestring.style.linestyle.color = "FF7800F0"


def doCarsMovement(stopSrc, stopDst, folder, playlist, firstPlacemark, kmlLines, addedLines, routeName, isLongTrip):

    startLatitude = float(stopSrc.stop_lat)
    startLongitude = float(stopSrc.stop_lon)
    objectiveLatitude = float(stopDst.stop_lat)
    objectiveLongitude = float(stopDst.stop_lon)
    addedLines[(stopSrc.stop_id, stopDst.stop_id)] = True

    zoomFactor = 1500000
    cameraRange = 1500000
    movementFactor = 100
    camera = 0.01

    latitudeModificator = (objectiveLatitude - startLatitude) / float(movementFactor)
    longitudeModificator = (objectiveLongitude - startLongitude) / float(movementFactor)

    incrementLatitude = True if latitudeModificator > 0 else False
    incrementLongitude = True if longitudeModificator > 0 else False

    logger.debug("Start Latitude: ", str(startLatitude))
    logger.debug("Start Longitude: ", str(startLongitude))
    logger.debug("Objective Latitude: ", str(objectiveLatitude))
    logger.debug("Objective Longitude: ", str(objectiveLongitude))
    logger.debug("Longitude Modificator: ", str(longitudeModificator))
    logger.debug("Latitude Modificator: ", str(latitudeModificator))

    latitudeAchieved = startLatitude >= objectiveLatitude if incrementLatitude else (
        startLatitude <= objectiveLatitude)
    longitudeAchieved = startLongitude >= objectiveLongitude if incrementLongitude else (
        startLongitude <= objectiveLongitude)

    counter = 0
    firstCarOfTrip = True
    while not latitudeAchieved and not longitudeAchieved:
        currentPoint = folder.newpoint(name=routeName)
        currentPoint.coords = [(startLongitude, startLatitude, 50000)]
        currentPoint.altitudemode = simplekml.AltitudeMode.relativetoground

        if firstPlacemark:
            firstPlacemark = False
            currentPoint.visibility = 1
        else:
            currentPoint.visibility = 0

        distance = getDistanceBetweenPoints(startLatitude, startLongitude, startLatitude + latitudeModificator,
                                            startLongitude + longitudeModificator)

        timeElapsed = distance / 800

        if distance < 300:
            timeElapsed = 0.001

        if isLongTrip:
            currentPoint.style.iconstyle.icon.href = 'files/trainBlue.png'
        else:
            currentPoint.style.iconstyle.icon.href = 'files/trainYellow.png'
        currentPoint.style.iconstyle.scale = 1

        if firstCarOfTrip:
            firstCarOfTrip = False
            doFlyTo(playlist, startLatitude, startLongitude, 750000, 750000, 3, 0)
            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=3.0)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility></Placemark>' \
                .format(currentPoint.placemark.id)

            playlist.newgxwait(gxduration=3.0)
        else:
            animatedupdateshow = playlist.newgxanimatedupdate(gxduration=timeElapsed)
            animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility></Placemark>' \
                .format(currentPoint.placemark.id)

            playlist.newgxwait(gxduration=timeElapsed)

        flyto = playlist.newgxflyto(gxduration=camera, gxflytomode=simplekml.GxFlyToMode.smooth)
        flyto.lookat.longitude = startLongitude
        flyto.lookat.latitude = startLatitude
        flyto.lookat.altitude = zoomFactor
        flyto.lookat.range = cameraRange
        playlist.newgxwait(gxduration=camera)

        animatedupdatehide = playlist.newgxanimatedupdate(gxduration=timeElapsed)
        animatedupdatehide.update.change = '<Placemark targetId="{0}"><visibility>0</visibility></Placemark>' \
            .format(currentPoint.placemark.id)

        playlist.newgxwait(gxduration=timeElapsed)

        doLines(stopSrc, stopDst, startLatitude, startLongitude,
                startLatitude+latitudeModificator,
                startLongitude+longitudeModificator,
                kmlLines)

        if not latitudeAchieved:
            startLatitude += latitudeModificator

        if not longitudeAchieved:
            startLongitude += longitudeModificator

        latitudeAchieved = startLatitude >= objectiveLatitude if incrementLatitude else (
            startLatitude <= objectiveLatitude)

        longitudeAchieved = startLongitude >= objectiveLongitude if incrementLongitude else (
            startLongitude <= objectiveLongitude)

        counter += 1

    playlist.newgxwait(gxduration=2)


def launchdemogtfs(request):
    millis = int(round(time.time() * 1000))
    command = "echo 'http://" + getDjangoIp() + ":"+getDjangoPort(request)+"/static/demos/lines_demo.kml?a="+str(millis) + \
              "\nhttp://" + getDjangoIp() + ":"+getDjangoPort(request)+"/static/demos/car_demo.kmz?a="+str(millis) +\
              "' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)
    time.sleep(5)
    playTour("GTFSTour")

    return HttpResponse(status=204)
