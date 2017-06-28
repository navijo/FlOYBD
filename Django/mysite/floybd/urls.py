import os

from django.conf.urls import url
from . import views
from .earthquakes import viewsEarthquakes
from .weather import viewsWeather
from .gtfs import viewsGTFS
from django.http import HttpResponseRedirect
from .models import Setting

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


    url(r'^heatMapEarthquakes', views.eartquakesHeatMapIndex, name='heatMapEarthquakes'),
    url(r'^getHeatMapEarthquakes', viewsEarthquakes.getHeatMap, name='getHeatMapEarthquakes'),


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


def createDefaultSettingsObjects():
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

startup_clean()
createDefaultSettingsObjects()
