
from django.shortcuts import render
from ..forms import UploadFileForm

import simplekml

import os
import shutil
import tarfile
import zipfile
import time
from ..utils import *
from .GTFSUtils import *
from ..gtfs_models import Agency
from .GTFSKMLWriter import *
from itertools import cycle

import xml.etree.ElementTree as ET

def uploadGTFS(request):
    if request.method == 'POST':
        title = request.POST['title']
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            millis = int(round(time.time() * 1000))
            form.title = title
            handle_uploaded_file(request.FILES['file'], form.title, millis)
            #kmlPath = handle_uploaded_file(request.FILES['file'], form.title, millis)
            #return render(request, 'floybd/gtfs/viewGTFS.html', {'form': form,'kml':kmlPath})
            agencies = Agency.objects.all()
            return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})
    else:
        form = UploadFileForm()
        return render(request, 'floybd/indexGTFS.html', {'form': form})


def handle_uploaded_file(f, title, millis):
    ip = getIp()
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
    #zipName = title+extension
    #kmlName = title+"_"+str(millis)+".kml"
    #kmlPath = "http://"+ip+":8000/static/kmls/" + kmlName

    #command = "python2 static/utils/gtfs/kmlwriter.py static/upload/gtfs/"+zipName+" static/kmls/"+kmlName
    #os.system(command)
    #return kmlPath


def parseGTFS(title):

    parseAgency("static/upload/gtfs/"+title)
    parseCalendar("static/upload/gtfs/"+title)
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
    print("Decompressing..."+extension)
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

    if not os.path.exists("static/upload/gtfs/"+title):
        os.makedirs("static/upload/gtfs/"+title)

    os.chdir("static/upload/gtfs/"+title)

    try:
        compressedFile = opener(file, mode)
        try:
            compressedFile.extractall()
        finally:
            compressedFile.close()
    finally:
        os.chdir(cwd)


def sendGTFSToLG(request):
    kmlPath = request.POST["kmlPath"]
    form = UploadFileForm()

    command = "echo '" + kmlPath + "' | sshpass -p lqgalaxy ssh lg@192.168.88.198 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    return render(request, 'floybd/gtfs/viewGTFS.html', {'form': form, 'kml': kmlPath})


def uploadgtfs(request):
    print("Upload GTFS")
    form = UploadFileForm()
    return render(request, 'floybd/gtfs/gtfsUpload.html', {'form': form})


def viewgtfs(request):
    print("View GTFS")
    agencies = Agency.objects.all()
    return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})


def getAgenciesAndGenerateKML1(request):
    agencies = request.POST.getlist('agenciesSelected')

    gtfsKml = simplekml.Kml()
    stops_folder = gtfsKml.newfolder(name='Stops')
    routes_folder = gtfsKml.newfolder(name='Routes')
    for selectedAgency in agencies:
        print("selectedAgency:" + str(selectedAgency))
        agency = Agency.objects.get(agency_id=selectedAgency)
        print("Agency:" + str(agency.agency_name))
        #getRoutesForAgency
        routes = Route.objects.filter(agency=agency)
        for route in routes:
            print("Route:" + str(route.route_long_name))
            # getTripForRoute
            trips = Trip.objects.filter(route_id=route.route_id)
            for trip in trips:
                print("Trip: " + str(trip.trip_id) + "\t" + str(trip.trip_headsign))
                #getCalendarForTrip
                calendar = Calendar.objects.filter(service_id=trip.service_id)
                #getCalendarInfo
                # getStopTimesForTrip
                stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
                for stop_time in stop_times:
                    print("Stop Time: " +
                          str(stop_time.arrival_time) +
                          "\t" +
                          str(stop_time.departure_time) +
                          "\t" +
                          str(stop_time.stop_id) +
                          "\n")
                    stop = stop_time.stop
                    print("Stop: " + str(stop.stop_name))
                   # for stop in stops:
                     #   print("Stop: " + str(stop.name))
                    stops_folder.newpoint(name=stop.stop_name, description=stop.stop_desc,
                                              coords=[(stop.stop_lon, stop.stop_lat)])


    kmlPath = "static/kmls/gtfs.kml"
    gtfsKml.save(kmlPath)

    agencies = Agency.objects.all()
    return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})
    #return kmlPath



def getAgenciesAndGenerateKML2(request):
    agencies = request.POST.getlist('agenciesSelected')

    doc = init()

    for selectedAgency in agencies:
        stopsList = []
        routesList = []
        print("selectedAgency:" + str(selectedAgency))
        agency = Agency.objects.get(agency_id=selectedAgency)
        print("Agency:" + str(agency.agency_name))
        routes = Route.objects.filter(agency=agency)
        for route in routes:
            print("Route:" + str(route.route_long_name))
            routesList.append(route)
            trips = Trip.objects.filter(route_id=route.route_id)
            print(type(trips))
            for trip in trips:
                print("Trip: " + str(trip.trip_id) + "\t" + str(trip.trip_headsign))
                stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
                for stop_time in stop_times:
                    stop = stop_time.stop
                    stopsList.append(stop)
                    print("Stop: " + str(stop.stop_name))

        createStopsFolder(doc, stopsList)
        CreateRoutesFolder(doc, routesList)

    SetIndentation(doc)
    end(doc, "gtfs")


    kmlPath = "static/kmls/gtfs.kml"


    agencies = Agency.objects.all()
    return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})


def getAgenciesAndGenerateKML(request):
    agencies = request.POST.getlist('agenciesSelected')

    calendars_added = []
    stops_added = []

    millis = int(round(time.time() * 1000))
    folderName = "static/kmls/"+str(millis)
    os.mkdir(folderName)

    flyToLatMax = 0
    flyToLatMin = 0
    flyToLonMax = 0
    flyToLonMin = 0

    agencies_file = open(folderName+"/agency.txt", 'w')
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
        agencyStr = str(agency.agency_url) +\
                    "," + str(agency.agency_name) + \
                    "," + str(agency.agency_id) + \
                    "," + str(agency.agency_timezone)+"\n"
        agencies_file.write(agencyStr)

        routes = Route.objects.filter(agency=agency)
        for route in routes:

            routeStr = str(route.route_type) + "," + str(route.route_id) + \
                        "," + str(route.route_short_name) + \
                        "," + str(route.route_long_name) + \
                        "," + str(route.agency_id)+"\n"

            routes_file.write(routeStr)

            trips = Trip.objects.filter(route_id=route.route_id)

            for trip in trips:
                tripStr = str(trip.route_id) + "," + str(trip.trip_id) + \
                           "," + str(trip.trip_headsign) + \
                           "," + str(trip.service_id)+"\n"

                trips_file.write(tripStr)

                if trip.service_id not in calendars_added:
                    calendars_added.append(trip.service_id)
                    calendar = Calendar.objects.get(service_id=trip.service_id)

                    calendarStr = str(calendar.service_id) +\
                                      "," + str(calendar.start_date.strftime("%Y%m%d")) + \
                                      "," + str(calendar.end_date.strftime("%Y%m%d")) + \
                                      (str(",1") if calendar.monday else (str(",0"))) + \
                                      (str(",1") if calendar.tuesday else (str(",0"))) + \
                                      (str(",1") if calendar.wednesday else (str(",0"))) + \
                                      (str(",1") if calendar.thursday else (str(",0"))) + \
                                      (str(",1") if calendar.friday else (str(",0"))) + \
                                      (str(",1") if calendar.saturday else (str(",0"))) + \
                                      (str(",1") if calendar.sunday else (str(",0"))) +\
                                        str("\n")
                    calendar_file.write(calendarStr)

                stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
                for stop_time in stop_times:
                    stop_times_str = str(stop_time.trip.trip_id) +\
                                      "," + str(stop_time.arrival_time) + \
                                      "," + str(stop_time.departure_time) + \
                                      "," + str(stop_time.stop_id) + \
                                      "," + str(stop_time.stop_sequence) + \
                                      "," + str(stop_time.stop_headsign) + \
                                      "," + str(stop_time.pickup_type) + \
                                      "," + str(stop_time.drop_off_type)+ \
                                      "," + str("0")+"\n"

                    stops_times_file.write(stop_times_str)

                    stop = stop_time.stop
                    if stop.stop_id not in stops_added:
                        print("Added Stop:" +stop.stop_id )
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
                      "," +str(stop.stop_lat) + \
                      "," +str(stop.stop_id) + \
                      "," +str(stop.location_type)+"\n"
            stops_file.write(stopStr)

    agencies_file.close()
    calendar_file.close()
    routes_file.close()
    stops_file.close()
    stops_times_file.close()
    trips_file.close()

    shutil.make_archive(folderName, 'zip', folderName)

    zipName = folderName+".zip"
    kmlName = str(millis)+".kml"


    command1 = "python2 static/utils/gtfs/kmlwriter.py "+zipName+" static/kmls/"+kmlName
    os.system(command1)

    ip = getIp()
    #Javi : 192.168.88.234
    #Gerard: 192.168.88.198
    lgIp = "192.168.88.234"

    carKml = extractLinesCoordinates("static/kmls/"+kmlName, millis)

    flyToLon = (flyToLonMax + flyToLonMin)/2
    flyToLat = (flyToLatMax + flyToLatMin) / 2

    flyTo = "flytoview=<LookAt>" \
            + "<longitude>" + str(flyToLon) + "</longitude>" \
            + "<latitude>" + str(flyToLat) + "</latitude>" \
            + "<altitude>100</altitude>" \
            + "<heading>14</heading>" \
            + "<tilt>45</tilt>" \
            + "<range>200000</range>" \
            + "<altitudeMode>relativeToGround</altitudeMode>" \
            + "<gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode></LookAt>"

    command = "echo '" + flyTo + "' | sshpass -p lqgalaxy ssh lg@"+lgIp+" 'cat - > /tmp/query.txt'"
    os.system(command)

    time.sleep(5)
    command = "echo 'http://" + ip + ":8000/static/kmls/" + kmlName + \
              "\nhttp://" + ip + ":8000/static/kmls/" + carKml + \
              "' | sshpass -p lqgalaxy ssh lg@" + lgIp + " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    time.sleep(1)
    command = "echo 'playtour=GTFSTour' | sshpass -p lqgalaxy ssh lg@"+lgIp+" 'cat - > /tmp/query.txt'"
    os.system(command)

    return render(request, 'floybd/gtfs/viewGTFS.html', {'kml': 'http://'+ip+':8000/static/kmls/' + kmlName})

def extractLinesCoordinates(filePath, millis):

    kml = simplekml.Kml()

    tree = ET.parse(filePath)
    lineStrings = tree.findall('.//{http://earth.google.com/kml/2.1}LineString')
    counter = 0
    cars = {}
    print("We have " + str(len(lineStrings))+" lines")
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

    newKmlName = "car_" + str(millis) + ".kml"
    kml1 = simplekml.Kml()

    tour1 = kml1.newgxtour(name="GTFSTour")

    playlist1 = tour1.newgxplaylist()
    folder = kml1.newfolder(name="Cars")
    firstPlacemark = True
    for key, value in cars.items():
        numberOfItems = len(value)
        for index, current in enumerate(value):
            if index+1 >= numberOfItems:
                break
            nextelem = value[index + 1]

            pLatitude = str(current.coords).split(",")[1]
            pLongitude = str(current.coords).split(",")[0]
            pNLatitude = str(nextelem.coords).split(",")[1]
            pNLongitude = str(nextelem.coords).split(",")[0]

            startLatitude = float(pLatitude)
            startLongitude = float(pLongitude)
            objectiveLatitude = float(pNLatitude)
            objectiveLongitude = float(pNLongitude)

            latitudeModificator = (objectiveLatitude - startLatitude)/50
            longitudeModificator = (objectiveLongitude - startLongitude)/50

            incrementLatitude = True if latitudeModificator > 0 else False
            incrementLongitude = True if longitudeModificator > 0 else False

            print("Start latitude:", str(startLatitude))
            print("Start longitude:", str(startLongitude))
            print("Objective latitude:", str(objectiveLatitude))
            print("Objective longitude:", str(objectiveLongitude))
            print("longitudeModificator:", str(longitudeModificator))
            print("latitudeModificator:", str(latitudeModificator))

            latitudeAchieved = startLatitude >= objectiveLatitude if incrementLatitude else (startLatitude <= objectiveLatitude)
            longitudeAchieved = startLongitude >= objectiveLongitude if incrementLongitude else (startLongitude <= objectiveLongitude)
            currentPoint = None
            while not latitudeAchieved and not longitudeAchieved:

                currentPoint = folder.newpoint(name='Car')
                currentPoint.coords = [(startLongitude, startLatitude)]
                if firstPlacemark:
                    firstPlacemark = False
                    currentPoint.visibility = 1
                else:
                    currentPoint.visibility = 0
                currentPoint.style.iconstyle.icon.href = 'https://mt.googleapis.com/vt/icon/name=icons/onion/27-cabs.png'

                animatedupdateshow = playlist1.newgxanimatedupdate(gxduration=0.1)
                animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility></Placemark>' \
                    .format(currentPoint.placemark.id)

                animatedupdatehide = playlist1.newgxanimatedupdate(gxduration=0.1)
                animatedupdatehide.update.change = '<Placemark targetId="{0}"><visibility>0</visibility></Placemark>' \
                    .format(currentPoint.placemark.id)

                playlist1.newgxwait(gxduration=0.1)

                if not latitudeAchieved:
                    startLatitude += latitudeModificator
                    print("Modified Start latitude:", str(startLatitude))

                if not longitudeAchieved:
                    startLongitude += longitudeModificator
                    print("Modified Start longitude:", str(startLongitude))

                latitudeAchieved = startLatitude >= objectiveLatitude if incrementLatitude else (
                startLatitude <= objectiveLatitude)

                longitudeAchieved = startLongitude >= objectiveLongitude if incrementLongitude else (
                startLongitude <= objectiveLongitude)

            playlist1.newgxwait(gxduration=3)

    print("Writing car file " + newKmlName)
    kml1.save("static/kmls/"+newKmlName)
    return newKmlName



def extractLinesCoordinates1(filePath, millis):
    newKmlName = "car_"+str(millis)+".kml"
    kml = simplekml.Kml()

    tour = kml.newgxtour(name="GTFSTour")

    playlist = tour.newgxplaylist()

    tree = ET.parse(filePath)
    lineStrings = tree.findall('.//{http://earth.google.com/kml/2.1}LineString')
    counter = 0
    for attributes in lineStrings:

        for subAttribute in attributes:
            if subAttribute.tag == '{http://earth.google.com/kml/2.1}coordinates':
                allCoords = subAttribute.text
                splittedPairsCoords = allCoords.split(" ")
                for pair in splittedPairsCoords:

                    lonLan = pair.split(",")

                    pnt = kml.newpoint(name='Car')
                    pnt.coords = [(lonLan[0], lonLan[1])]
                    pnt.visibility = 0
                    pnt.style.iconstyle.icon.href = 'https://mt.googleapis.com/vt/icon/name=icons/onion/27-cabs.png'

                    animatedupdateshow = playlist.newgxanimatedupdate(gxduration=1)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility></Placemark>' \
                        .format(pnt.placemark.id)


                    animatedupdatehide = playlist.newgxanimatedupdate(gxduration=1)
                    animatedupdatehide.update.change = '<Placemark targetId="{0}"><visibility>0</visibility></Placemark>' \
                        .format(pnt.placemark.id)




                    #print(subAttribute.tag, subAttribute.text)
                playlist.newgxwait(gxduration=3)
    kml.save("static/kmls/"+newKmlName)
    return newKmlName
