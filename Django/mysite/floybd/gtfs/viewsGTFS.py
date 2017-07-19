from django.shortcuts import render

from ..utils.gtfsUtils import *

from ..forms import UploadFileForm
from ..gtfs_models import Agency
from ..utils.lgUtils import *


import tarfile
import time
import zipfile
import simplekml
import random


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
        print("Creating upload/gtfs folder")
        os.makedirs("static/upload/gtfs")

    extension = get_extension(f)
    print("Extension:" + str(extension))
    if extension not in [".zip", ".tar", ".tgz"]:
        print("Saving normal File")
        saveNormalFile(f, title, extension)
    else:
        saveNormalFile(f, title, extension)
        decompressFile(f, title, extension)
        parseGTFS(title)

        # kmlwriter.py google_transit.zip googleTest.kml
        # zipName = title+extension
        # kmlName = title+"_"+str(millis)+".kml"
        # kmlPath = "http://"+ip+":8000/static/kmls/" + kmlName

        # command = "python2 static/utils/gtfs/kmlwriter.py static/upload/gtfs/"+zipName+" static/kmls/"+kmlName
        # os.system(command)
        # return kmlPath


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
    print("Decompressing..." + extension)
    if str(extension) == str('.zip'):
        print("Is Zip")
        opener, mode = zipfile.ZipFile, 'r'
    elif str(extension) == str('.tar.gz') or str(extension) == str('.tgz'):
        print("Is GZ")
        opener, mode = tarfile.open, 'r:gz'
    elif str(extension) == str('.tar.bz2') or str(extension) == str('.tbz'):
        print("Is Tar")
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

    command = "echo 'http://" + ip + ":8000/static/kmls/" + kmlName + \
              "\nhttp://" + ip + ":8000/static/kmls/" + carKml + \
              "' | sshpass -p lqgalaxy ssh lg@" + lgIp + " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    sendFlyToToLG(flyToLat, flyToLon, 6000000, 0, 0, 1, 4)

    time.sleep(5)
    playTour("GTFSTour")

    return render(request, 'floybd/gtfs/viewGTFS.html', {'kml': 'http://' + ip + ':8000/static/kmls/' + kmlName,
                                                         'flyToLon': flyToLon, 'flyToLat': flyToLat,
                                                         'carKml': carKml, 'kmlName': kmlName})


def uploadgtfs(request):
    print("Upload GTFS")
    form = UploadFileForm()
    return render(request, 'floybd/gtfs/gtfsUpload.html', {'form': form})


def viewgtfs(request):
    print("View GTFS")
    agencies = Agency.objects.all()
    return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})


def getAgenciesAndGenerateKML(request):
    agencies = request.POST.getlist('agenciesSelected')
    maxCars = int(request.POST.get('maxCars'))
    stops_added = []
    tripsAdded = []

    millis = int(round(time.time() * 1000))

    flyToLatMax = 0
    flyToLatMin = 0
    flyToLonMax = 0
    flyToLonMin = 0

    for selectedAgency in agencies:
        agency = Agency.objects.get(agency_id=selectedAgency)

        routes = Route.objects.filter(agency=agency)
        for route in routes:

            trips = Trip.objects.filter(route_id=route.route_id)

            for trip in trips:
                if trip.trip_id not in tripsAdded:
                    tripsAdded.append(trip)

                stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
                for stop_time in stop_times:
                    stop = stop_time.stop
                    if stop.stop_id not in stops_added:
                        print("Added Stop:" + stop.stop_id)
                        stops_added.append(stop.stop_id)

        for stop_id in stops_added:
            stop = Stop.objects.get(stop_id=stop_id)

            if flyToLatMax == 0:
                flyToLatMax = stop.stop_lat
                flyToLatMin = stop.stop_lat
            elif stop.stop_lat > flyToLatMax:
                flyToLatMax = stop.stop_lat
            elif stop.stop_lat < flyToLatMin:
                flyToLatMin = stop.stop_lat

            if flyToLonMax == 0:
                flyToLonMax = stop.stop_lon
                flyToLonMin = stop.stop_lon
            elif stop.stop_lon > flyToLonMax:
                flyToLonMax = stop.stop_lon
            elif stop.stop_lon < flyToLonMin:
                flyToLonMin = stop.stop_lon

    ip = getDjangoIp()

    linesKml, carKml = getAgenciesTrips(maxCars, tripsAdded, millis)

    flyToLon = (flyToLonMax + flyToLonMin) / 2
    flyToLat = (flyToLatMax + flyToLatMin) / 2

    return render(request, 'floybd/gtfs/viewGTFS.html', {'kml': 'http://' + ip + ':8000/static/kmls/' + linesKml,
                                                         'flyToLon': flyToLon, 'flyToLat': flyToLat,
                                                         'carKml': carKml, 'kmlName': linesKml})


def getAgenciesTrips(maxCars, trips, millis):
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
    for trip in trips:
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

            #doLines(stop1, stop2, kmlLines)


    while carsCounter < maxCars:
        #We take a random trip
        randomTrip = random.sample(trips, 1)
        #We get its stops
        stop_times = Stop_time.objects.filter(trip_id=randomTrip[0].trip_id)
        print("\tNew Car #", str(carsCounter))
        for index, current in enumerate(stop_times):
            if index + 1 >= len(stop_times):
                continue
            nextelem = stop_times[index + 1]

            stop1 = current.stop
            stop2 = nextelem.stop

            doCarsMovement(stop1, stop2, folderCars, playlistCars, firstPlacemark, kmlLines,addedLines)

            if firstPlacemark:
                firstPlacemark = False

        carsCounter += 1

    for trip in trips:
        stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
        for index, current in enumerate(stop_times):
            if index + 1 >= len(stop_times):
                continue
            nextelem = stop_times[index + 1]

            stop1 = current.stop
            stop2 = nextelem.stop
            key = (stop1.stop_id, stop2.stop_id)
            if key not in addedLines:
                print("\t Adding not included line")
                doLinesNotIncluded(stop1, stop2, kmlLines)

    kmlCarsName = "car_" + str(millis) + ".kmz"
    kmlLinesName = "lines_" + str(millis) + ".kml"
    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/img")
    imagePath = os.path.join(dir1, "train.png")
    print("Image located in ", imagePath)
    print("Cars to be added: " + str(maxCars))
    print("Cars really added: " + str(carsCounter))

    kmlCars.addfile(imagePath)
    kmlCars.savekmz("static/kmls/" + kmlCarsName, format=False)
    kmlLines.save("static/kmls/" + kmlLinesName)
    return kmlLinesName, kmlCarsName


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


def doCarsMovement(stopSrc, stopDst, folder, playlist, firstPlacemark, kmlLines, addedLines):

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

    print("Start Latitude: ", str(startLatitude))
    print("Start Longitude: ", str(startLongitude))
    print("Objective Latitude: ", str(objectiveLatitude))
    print("Objective Longitude: ", str(objectiveLongitude))
    print("Longitude Modificator: ", str(longitudeModificator))
    print("Latitude Modificator: ", str(latitudeModificator))

    latitudeAchieved = startLatitude >= objectiveLatitude if incrementLatitude else (
        startLatitude <= objectiveLatitude)
    longitudeAchieved = startLongitude >= objectiveLongitude if incrementLongitude else (
        startLongitude <= objectiveLongitude)

    counter = 0
    firstCarOfTrip = True
    while not latitudeAchieved and not longitudeAchieved:
        currentPoint = folder.newpoint(name='From '+str(stopSrc.stop_name)+' to '+str(stopDst.stop_name))
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

        currentPoint.style.iconstyle.icon.href = 'files/train.png'
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
            # print("Modified Start latitude:", str(startLatitude))

        if not longitudeAchieved:
            startLongitude += longitudeModificator
            # print("Modified Start longitude:", str(startLongitude))

        latitudeAchieved = startLatitude >= objectiveLatitude if incrementLatitude else (
            startLatitude <= objectiveLatitude)

        longitudeAchieved = startLongitude >= objectiveLongitude if incrementLongitude else (
            startLongitude <= objectiveLongitude)

        counter += 1

    playlist.newgxwait(gxduration=2)


