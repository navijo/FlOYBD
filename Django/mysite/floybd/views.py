from django.shortcuts import render
import os
import shutil
from django.http import HttpResponseRedirect
from .utils.utils import *


def index(request):
    return render(request, 'floybd/index.html')


def weatherIndex(request):
    return render(request, 'floybd/indexWeather.html')


def eartquakesIndex(request):
    return render(request, 'floybd/indexEarthquakes.html')

def eartquakesHeatMapIndex(request):
    return render(request, 'floybd/earthquakes/earthquakesHeatMap.html')

def gtfs(request):
    return render(request, 'floybd/indexGTFS.html')


def clearKML(request):
    print("Deletings kmls folder")
    shutil.rmtree('static/kmls')
    os.makedirs("static/kmls")

    command = "echo '' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def settingsIndex(request):
    settings = Setting.objects.all()
    return render(request, 'floybd/settings/settings.html', {'settings': settings})


