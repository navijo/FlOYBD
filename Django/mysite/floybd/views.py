from django.shortcuts import render
import os
import shutil
from .models import Setting


def index(request):
    return render(request, 'floybd/index.html')


def weatherIndex(request):
    return render(request, 'floybd/indexWeather.html')


def eartquakesIndex(request):
    return render(request, 'floybd/indexEarthquakes.html')


def gtfs(request):
    return render(request, 'floybd/indexGTFS.html')


def clearKML(request):
    print("Deletings kmls folder")
    shutil.rmtree('static/kmls')
    os.makedirs("static/kmls")
    return render(request, 'floybd/index.html')


def settingsIndex(request):
    settings = Setting.objects.all()
    return render(request, 'floybd/settings/settings.html', {'settings': settings})