from django.core.management.base import BaseCommand
from ...utils.lgUtils import *
from ...utils.earthquakesUtils import *
import requests
import json
from datetime import timedelta
import simplekml
from polycircles import polycircles
import datetime
from json.decoder import JSONDecodeError


class Command(BaseCommand):
    help = 'Generate Last Week Earthquakes KML'
    today = datetime.datetime.today()
    pastWeek = today - timedelta(days=7)
    pastWeekFormatted = pastWeek.strftime("%Y-%m-%d")

    def handle(self, *args, **options):
        self.generateLastWeekEarthquakesKml()
        self.stdout.write(self.style.SUCCESS('Generated Latest Week Earthquakes'))

    def generateLastWeekEarthquakesKml(self):
        self.stdout.write("Generating Latest Week Earthquakes KMZ... ")

        self.stdout.write("Getting Earthquakes")
        sparkIp = getSparkIp()

        response = requests.get('http://' + sparkIp + ':5000/getEarthquakes?date=' + self.pastWeekFormatted)

        jsonData = json.loads(response.json())
        numberObtained = len(jsonData)
        self.stdout.write("Obtained " + str(numberObtained) + " earthquakes")

        self.createKml(jsonData, numberObtained)

    def createKml(self, jsonData, numberObtained):
        kml = simplekml.Kml()

        tour = kml.newgxtour(name="LastWeekEarthquakesTour")
        playlist = tour.newgxplaylist()

        balloonDuration = 1
        flyToDuration = 3
        if numberObtained > 1000:
            balloonDuration = numberObtained / 1000

        self.stdout.write("Default duration: " + str(balloonDuration))
        earthquakeNumber = 1
        for row in jsonData:
            if earthquakeNumber > 666:
                break

            self.stdout.write(str(earthquakeNumber))

            place = row["place"]
            latitude = row["latitude"]
            longitude = row["longitude"]
            magnitude = row["magnitude"]
            try:
                geoJson = replaceJsonString(str(row["geojson"]))
                infowindow = self.populateInfoWindow(row, geoJson)
            except JSONDecodeError:
                self.stdout.write(self.style.ERROR('Error decoding json'))
                self.stdout.write(str(row["geojson"]))
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

                    pol.visibility = 0

                    ''' Fly To the atmosphere '''
                    flyto = playlist.newgxflyto(gxduration=flyToDuration,
                                                gxflytomode=simplekml.GxFlyToMode.smooth)
                    flyto.camera.longitude = longitude
                    flyto.camera.latitude = latitude
                    flyto.camera.altitude = 15000000
                    flyto.camera.range = 15000000
                    flyto.camera.tilt = 0
                    playlist.newgxwait(gxduration=flyToDuration)

                    ''' Go Back To the point '''
                    flyto = playlist.newgxflyto(gxduration=flyToDuration,
                                                gxflytomode=simplekml.GxFlyToMode.smooth)
                    flyto.camera.longitude = longitude
                    flyto.camera.latitude = latitude
                    flyto.camera.altitude = 100000
                    flyto.camera.range = 100000
                    flyto.camera.tilt = 0
                    playlist.newgxwait(gxduration=flyToDuration)

                    self.simulateEarthquake(playlist, latitude, longitude, absMagnitude)

                    animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration / 10)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}">' \
                                                       '<visibility>1</visibility></Placemark>' \
                        .format(pol.placemark.id)

                    for i in range(1, 11):
                        polycircleAux = polycircles.Polycircle(latitude=latitude, longitude=longitude,
                                                               radius=(200 * i) * absMagnitude,
                                                               number_of_vertices=100)

                        polAux = kml.newpolygon(name=place, outerboundaryis=polycircleAux.to_kml())
                        polAux.style.polystyle.color = color
                        polAux.style.polystyle.fill = 1
                        polAux.style.polystyle.outline = 1
                        polAux.style.linestyle.color = color
                        polAux.style.linestyle.width = 1
                        polAux.visibility = 0
                        polAux.style.balloonstyle.displaymode = simplekml.DisplayMode.hide

                        animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration / 10)
                        animatedupdateshow.update.change = '<Placemark targetId="{0}">' \
                                                           '<visibility>1</visibility></Placemark>' \
                            .format(polAux.placemark.id)

                        animatedupdatehide = playlist.newgxanimatedupdate(gxduration=balloonDuration / 10)
                        animatedupdatehide.update.change = '<Placemark targetId="{0}">' \
                                                           '<visibility>0</visibility></Placemark>' \
                            .format(polAux.placemark.id)

                        playlist.newgxwait(gxduration=balloonDuration / 10)

                    animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration * 2)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                                       '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
                        .format(pol.placemark.id)

                    playlist.newgxwait(gxduration=10)

                    animatedupdatehide = playlist.newgxanimatedupdate(gxduration=balloonDuration * 2)
                    animatedupdatehide.update.change = '<Placemark targetId="{0}">' \
                                                       '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                        .format(pol.placemark.id)

                    animatedupdateshow = playlist.newgxanimatedupdate(gxduration=balloonDuration / 10)
                    animatedupdateshow.update.change = '<Placemark targetId="{0}">' \
                                                       '<visibility>1</visibility></Placemark>' \
                        .format(pol.placemark.id)
            except ValueError:
                kml.newpoint(name=place, description=infowindow, coords=[(longitude, latitude)])
                self.stdout.write(str(absMagnitude))

            earthquakeNumber += 1

        playlist.newgxwait(gxduration=3 * balloonDuration)

        fileName = "lastWeekEarthquakes.kmz"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/demos")
        dirPath2 = os.path.join(dir1, fileName)
        self.stdout.write("Saving kml: " + str(dirPath2))
        if os.path.exists(dirPath2):
            os.remove(dirPath2)
        kml.savekmz(dirPath2, format=False)

    @staticmethod
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

    @staticmethod
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
