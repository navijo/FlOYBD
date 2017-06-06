from django.shortcuts import render
from .forms import UploadFileForm


def index(request):
    return render(request, 'floybd/index.html')


def weatherIndex(request):
    return render(request, 'floybd/indexWeather.html')


def eartquakesIndex(request):
    return render(request, 'floybd/indexEarthquakes.html')


def gtfs(request):
    return render(request, 'floybd/indexGTFS.html')
