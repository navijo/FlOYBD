from django.shortcuts import render
from django.contrib.staticfiles.templatetags.staticfiles import static
from ..utils.gtfsUtils import *
from .gtfsKMLWriter import *
from ..forms import UploadFileForm
from ..gtfs_models import Agency
from ..utils.lgUtils import *

import shutil
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

    sendFlyToToLG(flyToLat, flyToLon, 10, 14, 45, 20000, 4)

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
    calendars_added = []
    stops_added = []

    millis = int(round(time.time() * 1000))
    folderName = "static/kmls/" + str(millis)
    os.mkdir(folderName)

    flyToLatMax = 0
    flyToLatMin = 0
    flyToLonMax = 0
    flyToLonMin = 0

    agencies_file = open(folderName + "/agency.txt", 'w')
    agencies_file.write("agency_url,agency_name,agency_id,agency_timezone\n")

    calendar_file = open(folderName + "/calendar.txt", 'w')
    calendar_file.write("service_id,start_date,end_date,monday,tuesday,wednesday,thursday,friday,saturday,sunday\n")

    routes_file = open(folderName + "/routes.txt", 'w')
    routes_file.write("route_type,route_id,route_short_name,route_long_name,agency_id\n")

    stops_file = open(folderName + "/stops.txt", 'w')
    stops_file.write("stop_lon,stop_name,stop_lat,stop_id,location_type\n")

    stops_times_file = open(folderName + "/stop_times.txt", 'w')
    stops_times_file.write("trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,"
                           "drop_off_type,shape_dist_traveled\n")

    trips_file = open(folderName + "/trips.txt", 'w')
    trips_file.write("route_id,trip_id,trip_headsign,service_id\n")

    for selectedAgency in agencies:
        agency = Agency.objects.get(agency_id=selectedAgency)
        agencyStr = str(agency.agency_url) + \
                    "," + str(agency.agency_name) + \
                    "," + str(agency.agency_id) + \
                    "," + str(agency.agency_timezone) + "\n"
        agencies_file.write(agencyStr)

        routes = Route.objects.filter(agency=agency)
        for route in routes:

            routeStr = str(route.route_type) + "," + str(route.route_id) + \
                       "," + str(route.route_short_name) + \
                       "," + str(route.route_long_name) + \
                       "," + str(route.agency_id) + "\n"

            routes_file.write(routeStr)

            trips = Trip.objects.filter(route_id=route.route_id)

            for trip in trips:
                tripStr = str(trip.route_id) + "," + str(trip.trip_id) + \
                          "," + str(trip.trip_headsign) + \
                          "," + str(trip.service_id) + "\n"

                trips_file.write(tripStr)

                if trip.service_id not in calendars_added:
                    calendars_added.append(trip.service_id)
                    calendar = Calendar.objects.get(service_id=trip.service_id)

                    calendarStr = str(calendar.service_id) + \
                                  "," + str(calendar.start_date.strftime("%Y%m%d")) + \
                                  "," + str(calendar.end_date.strftime("%Y%m%d")) + \
                                  (str(",1") if calendar.monday else (str(",0"))) + \
                                  (str(",1") if calendar.tuesday else (str(",0"))) + \
                                  (str(",1") if calendar.wednesday else (str(",0"))) + \
                                  (str(",1") if calendar.thursday else (str(",0"))) + \
                                  (str(",1") if calendar.friday else (str(",0"))) + \
                                  (str(",1") if calendar.saturday else (str(",0"))) + \
                                  (str(",1") if calendar.sunday else (str(",0"))) + \
                                  str("\n")
                    calendar_file.write(calendarStr)

                stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
                for stop_time in stop_times:
                    stop_times_str = str(stop_time.trip.trip_id) + \
                                     "," + str(stop_time.arrival_time) + \
                                     "," + str(stop_time.departure_time) + \
                                     "," + str(stop_time.stop_id) + \
                                     "," + str(stop_time.stop_sequence) + \
                                     "," + str(stop_time.stop_headsign) + \
                                     "," + str(stop_time.pickup_type) + \
                                     "," + str(stop_time.drop_off_type) + \
                                     "," + str("0") + "\n"

                    stops_times_file.write(stop_times_str)

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

            stopStr = str(stop.stop_lon) + \
                      "," + str(stop.stop_name) + \
                      "," + str(stop.stop_lat) + \
                      "," + str(stop.stop_id) + \
                      "," + str(stop.location_type) + "\n"
            stops_file.write(stopStr)

    agencies_file.close()
    calendar_file.close()
    routes_file.close()
    stops_file.close()
    stops_times_file.close()
    trips_file.close()

    shutil.make_archive(folderName, 'zip', folderName)

    zipName = folderName + ".zip"
    kmlName = str(millis) + ".kml"

    command1 = "python2 static/utils/gtfs/kmlwriter.py " + zipName + " static/kmls/" + kmlName
    os.system(command1)

    ip = getDjangoIp()
    lgIp = getLGIp()

    carKml = extractLinesCoordinates("static/kmls/" + kmlName, millis, maxCars)

    flyToLon = (flyToLonMax + flyToLonMin) / 2
    flyToLat = (flyToLatMax + flyToLatMin) / 2

    return render(request, 'floybd/gtfs/viewGTFS.html', {'kml': 'http://' + ip + ':8000/static/kmls/' + kmlName,
                                                         'flyToLon': flyToLon, 'flyToLat': flyToLat,
                                                         'carKml': carKml, 'kmlName': kmlName})


def extractLinesCoordinates(filePath, millis, maxCars):
    kml = simplekml.Kml()

    tree = ET.parse(filePath)
    lineStrings = tree.findall('.//{http://earth.google.com/kml/2.1}LineString')
    counter = 0
    cars = {}
    print("We have " + str(len(lineStrings)) + " lines")
    carCounter = 0
    for attributes in lineStrings:

        for subAttribute in attributes:
            if subAttribute.tag == '{http://earth.google.com/kml/2.1}coordinates':
                linePoints = []
                allCoords = subAttribute.text
                splittedPairsCoords = allCoords.split(" ")
                for pair in splittedPairsCoords:
                    counter += 1
                    if counter % 2 == 0:
                        continue

                    lonLan = pair.split(",")

                    pnt = kml.newpoint(name='Car')
                    pnt.coords = [(lonLan[0], lonLan[1])]
                    pnt.visibility = 0
                    pnt.style.iconstyle.icon.href = 'https://mt.googleapis.com/vt/icon/name=icons/onion/27-cabs.png'

                    if pnt not in linePoints:
                        linePoints.append(pnt)
                cars[carCounter] = linePoints
        carCounter += 1

    newKmlName = "car_" + str(millis) + ".kmz"
    kml1 = simplekml.Kml()
    tour1 = kml1.newgxtour(name="GTFSTour")
    playlist1 = tour1.newgxplaylist()
    folder1 = kml1.newfolder(name="Cars")
    print("Total Cars: ", carCounter)
    firstPlacemark = True

    if maxCars >= carCounter:
        maxCars = carCounter

    addedTrips = []
    carCounter = 0
    #Get maxCars random cars
    for key, value in random.sample(cars.items(), maxCars):
        carCounter += 1
        numberOfItems = len(value)

        for index, current in enumerate(value):
            if index + 1 >= numberOfItems:
                continue
            nextelem = value[index + 1]

            pLatitude = str(current.coords).split(",")[1]
            pLongitude = str(current.coords).split(",")[0]
            pNLatitude = str(nextelem.coords).split(",")[1]
            pNLongitude = str(nextelem.coords).split(",")[0]

            startLatitude = float(pLatitude)
            startLongitude = float(pLongitude)
            objectiveLatitude = float(pNLatitude)
            objectiveLongitude = float(pNLongitude)

            distance = getDistanceBetweenPoints(startLatitude, startLongitude, objectiveLatitude, objectiveLongitude)

            movementFactor = 100
            zoomFactor = 50000
            cameraRange = 30000
            camera = 0.1

            if distance == 0:
                print("Distance 0")
                continue
            elif 500 < distance < 1000:
                print("Distance between 500 and 1000")
                movementFactor = 70
                zoomFactor = 1500000
                cameraRange = 1500000
                camera = 0.01
            elif 1000 < distance < 2000:
                print("Distance between 1000 and 2000")
                zoomFactor = 1500000
                cameraRange = 1500000
                movementFactor = 80
                camera = 0.01
            elif distance > 2000:
                print("Distance over 2000")
                zoomFactor = 1500000
                cameraRange = 1500000
                movementFactor = 90
                camera = 0.01

            zoomFactor = 1500000
            cameraRange = 1500000
            movementFactor = 90
            camera = 0.01

            if [startLatitude, startLongitude, objectiveLatitude, objectiveLongitude] not in addedTrips:
                addedTrips.append([startLatitude, startLongitude, objectiveLatitude, objectiveLongitude])

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

                while not latitudeAchieved and not longitudeAchieved:
                    currentPoint = folder1.newpoint(name='Car')
                    currentPoint.coords = [(startLongitude, startLatitude)]
                    if firstPlacemark:
                        firstPlacemark = False
                        currentPoint.visibility = 1
                    else:
                        currentPoint.visibility = 0

                    distance = getDistanceBetweenPoints(startLatitude, startLongitude, startLatitude+latitudeModificator,
                                                        startLongitude+longitudeModificator)

                    #800 m/h * 1h/3600s
                    speedFactor = 800/3600
                    #timeElapsed = distance/speedFactor
                    timeElapsed = distance / 800
                    #camera = 0.03

                    if distance < 300:
                        timeElapsed = 0.001

                    currentPoint.style.iconstyle.icon.href = 'files/train.png'
                    currentPoint.style.iconstyle.scale = 1

                    animatedupdateshow = playlist1.newgxanimatedupdate(gxduration=timeElapsed)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility></Placemark>' \
                        .format(currentPoint.placemark.id)

                    playlist1.newgxwait(gxduration=timeElapsed)

                    flyto = playlist1.newgxflyto(gxduration=camera, gxflytomode=simplekml.GxFlyToMode.smooth)
                    flyto.lookat.longitude = startLongitude
                    flyto.lookat.latitude = startLatitude
                    flyto.lookat.altitude = zoomFactor
                    flyto.lookat.range = cameraRange
                    playlist1.newgxwait(gxduration=camera)

                    animatedupdatehide = playlist1.newgxanimatedupdate(gxduration=timeElapsed)
                    animatedupdatehide.update.change = '<Placemark targetId="{0}"><visibility>0</visibility></Placemark>' \
                        .format(currentPoint.placemark.id)

                    playlist1.newgxwait(gxduration=timeElapsed)

                    if not latitudeAchieved:
                        startLatitude += latitudeModificator
                        #print("Modified Start latitude:", str(startLatitude))

                    if not longitudeAchieved:
                        startLongitude += longitudeModificator
                       # print("Modified Start longitude:", str(startLongitude))

                    latitudeAchieved = startLatitude >= objectiveLatitude if incrementLatitude else (
                        startLatitude <= objectiveLatitude)

                    longitudeAchieved = startLongitude >= objectiveLongitude if incrementLongitude else (
                        startLongitude <= objectiveLongitude)

                    counter += 1

                playlist1.newgxwait(gxduration=2)

    print("Total Cars Added: ", carCounter)
    print("Writing car file " + newKmlName)

    currentDir = os.getcwd()
    dir1 = os.path.join(currentDir, "static/img")
    imagePath = os.path.join(dir1, "train.png")
    print("Image located in ", imagePath)

    kml1.addfile(imagePath)
    kml1.savekmz("static/kmls/" + newKmlName, format=False)
    return newKmlName

