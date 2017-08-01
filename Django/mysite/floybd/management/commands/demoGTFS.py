from django.core.management.base import BaseCommand
from ...utils.lgUtils import *
from ...utils.gtfsUtils import *
import random
from ...gtfs_models import *

import time



class Command(BaseCommand):
    help = 'Generate Dummy GTFS KML'

    def handle(self, *args, **options):
        self.generateDummyWeatherKml()
        self.stdout.write(self.style.SUCCESS('Generated Dummy GTFS File'))

    def generateDummyWeatherKml(self):
        self.stdout.write("Generating Dummy GTFS KMZ... ")
        maxCars = 20
        stops_added = []
        tripsAdded = []

        millis = int(round(time.time() * 1000))

        agency = Agency.objects.get(agency_id="US_Agency")

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
                        self.stdout.write("Added Stop:" + stop.stop_id)
                        stops_added.append(stop.stop_id)

        self.getAgenciesTrips(maxCars, tripsAdded, millis)

    def getAgenciesTrips(self, maxCars, trips, millis):
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
                    self.doPlacemarks(stop1, kmlLines)
                if stop2 not in addedStops:
                    addedStops.append(stop2)
                    self.doPlacemarks(stop2, kmlLines)

                    # doLines(stop1, stop2, kmlLines)

        while carsCounter < maxCars:
            # We take a random trip
            randomTrip = random.sample(trips, 1)
            # We get its stops
            stop_times = Stop_time.objects.filter(trip_id=randomTrip[0].trip_id)
            self.stdout.write("\tNew Car #" + str(carsCounter))

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
                    self.stdout.write(
                        "\t Found long trip with " + str(len(stop_times)) + " stops. From " + stopSrc.stop_name + " to "
                        + stopDst.stop_name)
                    isLongTrip = True
                else:
                    routeName = 'From ' + str(stop1.stop_name) + ' to ' + str(stop2.stop_name)
                    isLongTrip = False

                self.doCarsMovement(stop1, stop2, folderCars, playlistCars, firstPlacemark, kmlLines, addedLines, routeName,
                               isLongTrip)

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
                    self.stdout.write("\t Adding not included line")
                    self.doLinesNotIncluded(stop1, stop2, kmlLines)

        kmlCarsName = "car_demo.kmz"
        kmlLinesName = "lines_demo.kml"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/img")
        imagePath = os.path.join(dir1, "trainYellow.png")
        imagePath2 = os.path.join(dir1, "trainBlue.png")
        self.stdout.write("Image located in " + str(imagePath))
        self.stdout.write("Cars to be added: " + str(maxCars))
        self.stdout.write("Cars really added: " + str(carsCounter))

        kmlCars.addfile(imagePath)
        kmlCars.addfile(imagePath2)

        kmlCars.savekmz("static/demos/" + kmlCarsName, format=False)
        kmlLines.save("static/demos/" + kmlLinesName)
        return kmlLinesName, kmlCarsName

    def doPlacemarks(self, stop, kmlTrips):
        point = kmlTrips.newpoint(name=stop.stop_name + " HUB")
        point.coords = [(stop.stop_lon, stop.stop_lat, 50000)]
        point.altitudemode = simplekml.AltitudeMode.relativetoground
        point.extrude = 1
        point.linestyle.width = 20
        point.style.labelstyle.scale = 1.5
        point.style.labelstyle.color = simplekml.Color.blue
        point.style.linestyle.color = simplekml.Color.blue
        point.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/shapes/subway.png"

    @staticmethod
    def doLinesNotIncluded(stopSrc, stopDst, kmlTrips):

        linestring = kmlTrips.newlinestring(name='From ' + str(stopSrc.stop_name) + ' to ' + str(stopDst.stop_name))
        linestring.coords = [(stopSrc.stop_lon, stopSrc.stop_lat, 50000), (stopDst.stop_lon, stopDst.stop_lat, 50000)]
        linestring.altitudemode = simplekml.AltitudeMode.relativetoground
        linestring.tesellate = 1
        linestring.style.linestyle.width = 15
        linestring.style.linestyle.color = "FF7800F0"

    @staticmethod
    def doLines(stopSrc, stopDst, startLat, startLon, dstLat, dstLon, kmlTrips):

        linestring = kmlTrips.newlinestring(name='From ' + str(stopSrc.stop_name) + ' to ' + str(stopDst.stop_name))
        linestring.coords = [(startLon, startLat, 50000), (dstLon, dstLat, 50000)]
        linestring.altitudemode = simplekml.AltitudeMode.relativetoground
        linestring.tesellate = 1
        linestring.style.linestyle.width = 15
        linestring.style.linestyle.color = "FF7800F0"

    def doCarsMovement(self, stopSrc, stopDst, folder, playlist, firstPlacemark, kmlLines, addedLines, routeName, isLongTrip):

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

            self.doLines(stopSrc, stopDst, startLatitude, startLongitude,
                    startLatitude + latitudeModificator,
                    startLongitude + longitudeModificator,
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
