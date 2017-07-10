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

app_name = 'floybd'


urlpatterns = [

    url(r'^$', views.index, name='index'),

    url(r'clearKML', views.clearKML, name='clearKML'),
    url(r'^weatherStats', viewsWeather.weatherStats, name='weatherStats'),
    url(r'^dayWeather', viewsWeather.weatherConcreteIndex, name='dayWeather'),
    url(r'^predictWeatherStats', viewsWeather.weatherPredictionsStats, name='predictWeatherStats'),
    url(r'^predictWeather', viewsWeather.weatherPredictions, name='predictWeather'),
    url(r'^weather', views.weatherIndex, name='weather'),

    url('getConcreteDateValues', viewsWeather.getConcreteValues, name='getConcreteDateValues'),
    url('sendConcreteValuesToLG', viewsWeather.sendConcreteValuesToLG, name='sendConcreteValuesToLG'),
    url('getPredictionStats', viewsWeather.getPredictionStats, name='getPredictionStats'),
    url('getPrediction', viewsWeather.getPrediction, name='getPrediction'),
    url('sendPredictionsToLG', viewsWeather.sendPredictionsToLG, name='sendPredictionsToLG'),

    url(r'^earthquakes/$', views.eartquakesIndex, name='earthquakes'),
    url('getEarthquakes', viewsEarthquakes.getEarthquakes, name='getEarthquakes'),
    url('sendConcreteEarthquakesValuesToLG', viewsEarthquakes.sendConcreteValuesToLG,
        name='sendConcreteEarthquakesValuesToLG'),


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

    url('settings', lambda x: HttpResponseRedirect('/admin/floybd/setting/'), name='settings'),
]


def sendLogos():
    #getLeftScreenCommand = "sshpass -p " + getLGPass() + " ssh lg@" + getLGIp() + " 'head -n 1 personavars.txt | cut -c17-19'"
    #leftScreenDirty = subprocess.check_output(getLeftScreenCommand, stderr=subprocess.STDOUT, shell=True)
    #leftScreenClean = leftScreenDirty.rstrip().decode("utf-8")
    #print("Left Screen: ", leftScreenClean)

    if db_table_exists("floybd_setting"):
        if checkPing(getLGIp()):
            print("Sending Logos...")
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
