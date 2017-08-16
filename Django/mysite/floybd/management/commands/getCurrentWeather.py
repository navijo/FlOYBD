from django.core.management.base import BaseCommand
from ...utils.lgUtils import *
import requests
from collections import defaultdict
import json
import time
import datetime

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Command(BaseCommand):
    help = 'Generate Dummy Weather KML'

    def handle(self, *args, **options):
        self.generateDummyWeatherKml()
        self.stdout.write(self.style.SUCCESS('Generated Dummy Weather File'))

    def generateDummyWeatherKml(self):
        self.stdout.write("Generating Dummy Weather KMZ... ")
        response = requests.get('http://' + getSparkIp() + ':5000/getKey',
                                headers={'Accept': 'application/json', 'Content-Type': 'application/json'})

        api_key_resp = response.json()
        api_key = api_key_resp[0]['api_key']

        querystring = {"api_key": api_key}
        headers = {'cache-control': "no-cache"}
        base_url = "https://opendata.aemet.es/opendata"

        currentWeather = self.getData(base_url + "/api/observacion/convencional/todas", headers, querystring)

        stationsDict = defaultdict(list)
        self.stdout.write("Parsing current weather... ")
        kml = simplekml.Kml()
        tourCurrentWeather = kml.newgxtour(name="Tour Current Weather")
        playlistCurrentWeather = tourCurrentWeather.newgxplaylist()

        for row in currentWeather:
            jsonData = json.loads(json.dumps(row))
            stationId = jsonData.get("idema")
            stationsDict[stationId].append(jsonData)

        self.stdout.write("Generating current weather kmz... ")

        totalStations = len(stationsDict.items())
        stationNumber = 1

        doFlyToSmooth(playlistCurrentWeather, 42.305568, -1.985615, 0, 4855570, 3.0, 0)

        for key, value in stationsDict.items():
            actualPercentage = (stationNumber / totalStations) * 100
            self.stdout.write(str(actualPercentage))

            jsonData = json.loads(json.dumps(value[-1]))
            latitude = float(jsonData.get("lat"))
            longitude = float(jsonData.get("lon"))
            datetimeStr = datetime.datetime.strptime(jsonData.get("fint"), "%Y-%m-%dT%H:%M:%S").\
                strftime('%H:%M:%S %Y-%m-%d')

            contentString = '<link rel = "stylesheet" href = "' \
                            'https://code.getmdl.io/1.3.0/material.blue_grey-red.min.css" / > ' \
                            '<link rel="stylesheet" href="https://fonts.googleapis.com/css?' \
                            'family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&lang=en"/>' +\
                            '<table width="470" style="font-family: Roboto;"><tr><td>' +\
                            '<div id="content">' + '<div id="siteNotice">' + '</div>' +\
                            '<h1 id="firstHeading" class="firstHeading" style="text-align:center">' +\
                            jsonData.get("ubi") + '</h1>' + \
                            '<h2 id="firstHeading" class="secondHeading" style="text-align:center">Station ID: ' +\
                            jsonData.get("idema") + '</h2>' +\
                            '<h3 id="firstHeading" class="thirdHeading" style="text-align:center">Date: ' +\
                            datetimeStr + '</h3>' +\
                            '<div id="bodyContent" style="text-align: center;">' +\
                            '<div class="demo-charts mdl-color--white mdl-shadow--2dp ' \
                            'mdl-cell mdl-cell--6-col mdl-grid" style="width: 98%">' +\
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' +\
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">Max Temp:</p>' +\
                            '</div>' +\
                            '<div class="mdl-cell mdl-cell--3-col mdl-layout-spacer">' +\
                            '<p style="font-size:1.5em;color:#474747;line-height:0.5;">' +\
                            str(jsonData.get("tamax")) + ' ºC</p>' +\
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
                            '</div>' +\
                            '</div></div>' +\
                            '</td></tr></table>'

            point = kml.newpoint(name=jsonData.get("ubi"), description=contentString,coords=[(longitude, latitude)])

            point.style.balloonstyle.bgcolor = simplekml.Color.lightblue
            point.style.balloonstyle.text = contentString
            point.gxballoonvisibility = 0
            point.style.iconstyle.icon.href = 'https://png.icons8.com/thermometer-automation/ultraviolet/80'

            if stationNumber % 3 == 0:
                doFlyToSmooth(playlistCurrentWeather, latitude, longitude, 0, 4855570, 3.0, 0)
                playlistCurrentWeather.newgxwait(gxduration=3.0)
                doFlyToSmooth(playlistCurrentWeather, latitude, longitude, 1000, 5000, 5.0, 0)
                playlistCurrentWeather.newgxwait(gxduration=5.0)
                doFlyToSmooth(playlistCurrentWeather, latitude, longitude, 1000, 5000, 1)
                playlistCurrentWeather.newgxwait(gxduration=1)

                animatedupdateshow = playlistCurrentWeather.newgxanimatedupdate(gxduration=5.0)
                animatedupdateshow.update.change = '<Placemark targetId="{0}"><visibility>1</visibility>' \
                                                   '<gx:balloonVisibility>1</gx:balloonVisibility></Placemark>' \
                    .format(point.placemark.id)

                doRotation(playlistCurrentWeather, latitude, longitude, 1000, 5000)

                animatedupdateshow = playlistCurrentWeather.newgxanimatedupdate(gxduration=0.1)
                animatedupdateshow.update.change = '<Placemark targetId="' \
                                                   '{0}"><visibility>0</visibility>' \
                                                   '<gx:balloonVisibility>0</gx:balloonVisibility></Placemark>' \
                    .format(point.placemark.id)
                playlistCurrentWeather.newgxwait(gxduration=0.1)

            stationNumber += 1

        fileName = "dummyWeather.kmz"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/demos")
        dirPath2 = os.path.join(dir1, fileName)

        kml.savekmz(dirPath2, format=False)

    def getData(self, url, headers, querystring):
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
                    self.stdout.write("####Sleeping")
                    time.sleep(60)
                    self.stdout.write("####Waked up!!")
                    return self.getData(url)
        except requests.exceptions.ConnectionError:
            self.stdout.write("####ERROR!! => Sleeping")
            time.sleep(120)
            self.stdout.write("####Waked up!!")
            return self.getData(url)


