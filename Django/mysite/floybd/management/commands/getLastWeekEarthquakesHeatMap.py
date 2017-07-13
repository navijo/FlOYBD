from django.core.management.base import BaseCommand
from ...utils.lgUtils import *
import requests
import json
from datetime import timedelta
import time
from ...utils.cylinders.cylindersHeatMap import *
import datetime


class Command(BaseCommand):
    help = 'Generate Last Week Earthquakes Heatmap KML'
    today = datetime.datetime.today()
    pastWeek = today - timedelta(days=7)
    pastWeekFormatted = pastWeek.strftime("%Y-%m-%d")

    def handle(self, *args, **options):
        self.generateLastWeekEarthquakesKml()
        self.stdout.write(self.style.SUCCESS('Generated Latest Week Earthquakes Heatmap'))

    def generateLastWeekEarthquakesKml(self):
        self.stdout.write("Generating Latest Week Earthquakes Heatmap KMZ... ")

        self.stdout.write("Generating HeatMap")

        response = requests.get('http://' + getSparkIp() + ':5000/getEarthquakes?date=' + self.pastWeekFormatted)

        jsonData = json.loads(response.json())

        numberObtained = len(jsonData)
        self.stdout.write("Obtained " + str(numberObtained) + " earthquakes")

        data = self.getEartquakesArray(jsonData)

        fileName = "lastWeekEarthquakesHeatMap.kmz"
        currentDir = os.getcwd()
        dir1 = os.path.join(currentDir, "static/demos")
        dirPath2 = os.path.join(dir1, fileName)

        cylinder = CylindersKmlHeatmap(fileName, data)
        cylinder.makeKMZ(dirPath2)
        time.sleep(2)

    def getEartquakesArray(self, jsonData):
        data = []
        for row in jsonData:
            data.append([row.get("latitude"), row.get("longitude"), row.get("magnitude"), row.get("place"),
                         row.get("fecha")])
        return data
