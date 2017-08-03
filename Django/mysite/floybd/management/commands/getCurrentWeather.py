from django.core.management.base import BaseCommand
from ...utils.lgUtils import *
import requests
from collections import defaultdict
import json
import time

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

        for key, value in stationsDict.items():
            actualPercentage = (stationNumber / totalStations) * 100
            self.stdout.write(str(actualPercentage))

            jsonData = json.loads(json.dumps(value[-1]))
            latitude = float(jsonData.get("lat"))
            longitude = float(jsonData.get("lon"))

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
            point.gxballoonvisibility = 0
            point.style.iconstyle.icon.href = 'https://png.icons8.com/thermometer-automation/ultraviolet/80'

            doFlyTo(playlistCurrentWeather, latitude, longitude, 1000, 5000, 3.0)
            playlistCurrentWeather.newgxwait(gxduration=3.0)

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


