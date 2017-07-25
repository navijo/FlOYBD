import os

from django.conf.urls import url
from . import views
from .earthquakes import viewsEarthquakes
from .weather import viewsWeather
from .gtfs import viewsGTFS
from django.http import HttpResponseRedirect
from .models import Setting
from .utils.utils import *
import subprocess
from django.db import connection
import simplekml
import time


app_name = 'floybd'


urlpatterns = [

    url(r'^$', views.index, name='index'),

    url('clearKML', views.clearKML, name='clearKML'),
    url('weatherStats', viewsWeather.weatherStats, name='weatherStats'),
    url('dayWeather', viewsWeather.weatherConcreteIndex, name='dayWeather'),
    url('predictWeatherStats', viewsWeather.weatherPredictionsStats, name='predictWeatherStats'),
    url('predictWeather', viewsWeather.weatherPredictions, name='predictWeather'),
    url('weatherDemos', views.weatherDemos, name='weatherDemos'),
    url('weather', views.weatherIndex, name='weather'),
    url('currentWeather', viewsWeather.currentWeather, name='currentWeather'),
    url('dummyWeather', viewsWeather.dummyWeather, name='dummyWeather'),
    url('stopTour', views.stopTourView, name='stopTour'),
    url('demoEarthquakes', views.demoEarthquakes, name='demoEarthquakes'),


    url('getConcreteDateValues', viewsWeather.getConcreteValues, name='getConcreteDateValues'),
    url('sendConcreteValuesToLG', viewsWeather.sendConcreteValuesToLG, name='sendConcreteValuesToLG'),
    url('getPredictionStats', viewsWeather.getPredictionStats, name='getPredictionStats'),
    url('getPrediction', viewsWeather.getPrediction, name='getPrediction'),
    url('sendPredictionsToLG', viewsWeather.sendPredictionsToLG, name='sendPredictionsToLG'),

    url('earthquakes', views.eartquakesIndex, name='earthquakes'),
    url('getApproxEarthquakes', viewsEarthquakes.getEarthquakesApprox, name='getApproxEarthquakes'),
    url('getExactEarthquakes', viewsEarthquakes.getEarthquakesExact, name='getExactEarthquakes'),
    url('sendConcreteEarthquakesValuesToLG', viewsEarthquakes.sendConcreteValuesToLG,
        name='sendConcreteEarthquakesValuesToLG'),

    url('demoLastWeekEarthquakesHeatmap', viewsEarthquakes.demoLastWeekEarthquakesHeatmap,
        name='demoLastWeekEarthquakesHeatmap'),
    url('demoLastWeekEarthquakes', viewsEarthquakes.demoLastWeekEarthquakes, name='demoLastWeekEarthquakes'),


    url('heatMapEarthquakes', views.eartquakesHeatMapIndex, name='heatMapEarthquakes'),
    url('getHeatMapEarthquakesKML', viewsEarthquakes.generateHeapMapKml, name='getHeatMapEarthquakesKML'),
    url('getHeatMapEarthquakes', viewsEarthquakes.getHeatMap, name='getHeatMapEarthquakes'),



    url('getStats', viewsWeather.getStats, name='getStats'),
    url('sendStatsToLG', viewsWeather.sendStatsToLG, name='sendStatsToLG'),
    url('getGraphDataForStats', viewsWeather.getGraphDataForStats, name='getGraphDataForStats'),

    url('uploadgtfs', viewsGTFS.uploadgtfs, name='uploadgtfs'),
    url('viewgtfs', viewsGTFS.viewgtfs, name='viewgtfs'),
    url('gtfs', views.gtfs, name='gtfs'),
    url('uploadGTFS', viewsGTFS.uploadGTFS, name='uploadGTFS'),
    url('sendGTFSToLG', viewsGTFS.sendGTFSToLG, name='sendGTFSToLG'),
    url('getAgenciesAndGenerateKML', viewsGTFS.getAgenciesAndGenerateKML,
        name='getAgenciesAndGenerateKML'),

    url('citydashboard', viewsWeather.citydashboard, name='citydashboard'),
    url('viewDashboard', viewsWeather.viewDashboard, name='viewDashboard'),

    url('openHelp', views.openHelp, name='openHelp'),
    url('launchScreenSaver', views.launchScreenSaver, name='launchScreenSaver'),
    url('stopScreenSaver', views.stopScreenSaver, name='stopScreenSaver'),
    url('clearCache', views.clearLGCache, name='clearCache'),
    url('relaunchLG', views.relaunchLG, name='relaunchLG'),

    url('settings', lambda x: HttpResponseRedirect('/admin/floybd/setting/'), name='settings'),



]


def sendLogos():
    #getLeftScreenCommand = "sshpass -p " + getLGPass() + " ssh lg@" + getLGIp() + " 'head -n 1 personavars.txt | cut -c17-19'"
    #leftScreenDirty = subprocess.check_output(getLeftScreenCommand, stderr=subprocess.STDOUT, shell=True)
    #leftScreenClean = leftScreenDirty.rstrip().decode("utf-8")
    #print("Left Screen: ", leftScreenClean)

    kml = simplekml.Kml(name="Layout")
    screen = kml.newscreenoverlay(name='FLOYBD')
    screen.icon.href = "http://"+getDjangoIp()+":8000/static/img/propis.png"
    screen.overlayxy = simplekml.OverlayXY(x=0.0, y=1.0, xunits=simplekml.Units.fraction,
                                           yunits=simplekml.Units.fraction)
    screen.screenxy = simplekml.ScreenXY(x=0.0, y=1.0, xunits=simplekml.Units.fraction,
                                         yunits=simplekml.Units.fraction)
    screen.rotationxy = simplekml.RotationXY(x=0.0, y=0.0, xunits=simplekml.Units.fraction,
                                         yunits=simplekml.Units.fraction)
    screen.size.x = 0.25
    screen.size.y = 0.2
    screen.size.xunits = simplekml.Units.fraction
    screen.size.yunits = simplekml.Units.fraction

    screen1 = kml.newscreenoverlay(name='Logos')
    screen1.icon.href = "http://" + getDjangoIp() + ":8000/static/img/comuns.png"
    screen1.overlayxy = simplekml.OverlayXY(x=0.0, y=0.0, xunits=simplekml.Units.fraction,
                                           yunits=simplekml.Units.fraction)
    screen1.screenxy = simplekml.ScreenXY(x=0.0, y=0.01, xunits=simplekml.Units.fraction,
                                         yunits=simplekml.Units.fraction)
    screen1.rotationxy = simplekml.RotationXY(x=0.0, y=0.0, xunits=simplekml.Units.fraction,
                                           yunits=simplekml.Units.fraction)
    screen1.size.x = 0.5
    screen1.size.y = 0.45
    screen1.size.xunits = simplekml.Units.fraction
    screen1.size.yunits = simplekml.Units.fraction

    currentDir = os.getcwd()
    fileName = "Layout.kml"
    dir1 = os.path.join(currentDir, "static/logos")
    dirPath2 = os.path.join(dir1, fileName)
    print("Saving kml: ", dirPath2)

    kml.save(dirPath2)

    if db_table_exists("floybd_setting"):
        if checkPing(getLGIp()):
            print("Sending Logos...from: " + getDjangoIp() + " to: " + getLGIp())
            command = "echo 'http://" + getDjangoIp() + ":8000/static/logos/Layout.kml" +\
                      "' | sshpass -p " + getLGPass() + " ssh lg@" + getLGIp() + " 'cat - > /var/www/html/kmls_4.txt'"

            os.system(command)


def createDefaultSettingsObjects():
    if db_table_exists("floybd_setting"):
        lgIp, created = Setting.objects.get_or_create(key="lgIp")
        if created:
            print("Created lgIp setting object\n")
        else:
            print("lgIp setting object existent\n")

        sparkIp, created = Setting.objects.get_or_create(key="sparkIp", value="130.206.117.178")
        if created:
            print("Created sparkIp setting object\n")
        else:
            print("sparkIp setting object existent\n")

        LGPassword, created = Setting.objects.get_or_create(key="LGPassword", value="lqgalaxy")
        if created:
            print("Created LGPassword setting object\n")
        else:
            print("LGPassword setting object existent\n")


def startup_clean():
    if not os.path.exists("static/kmls"):
        print("Creating kmls folder")
        os.makedirs("static/kmls")


def db_table_exists(table_name):
    print("Checking table existence...", table_name)
    return table_name in connection.introspection.table_names()


def checkPing(host):
    response = os.system("ping -c 1 " + host)

    if response == 0:
        print(host, 'is up!')
        return True
    else:
        print(host, 'is down!')
        return False


startup_clean()
createDefaultSettingsObjects()
sendLogos()
