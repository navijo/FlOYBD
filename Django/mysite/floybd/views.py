from django.shortcuts import render
import shutil
from .utils.lgUtils import *
from .utils.utils import *
import requests
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def index(request):
    return render(request, 'floybd/index.html')


def weatherIndex(request):
    return render(request, 'floybd/indexWeather.html')


def eartquakesIndex(request):
    return render(request, 'floybd/indexEarthquakes.html')


def eartquakesHeatMapIndex(request):
    return render(request, 'floybd/earthquakes/earthquakesHeatMap.html')


def demogtfs(request):
    return render(request, 'floybd/gtfs/demoGTFS.html')


def gtfs(request):
    return render(request, 'floybd/indexGTFS.html')


def clearKML(request):
    print("Deletings kmls folder")
    shutil.rmtree('static/kmls')
    os.makedirs("static/kmls")

    command = "echo '' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    for i in range(1, 6):
        command = "echo '' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
                  " 'cat - > /var/www/html/kmls_"+str(i)+".txt'"
        os.system(command)

    print("Deleting remote kmls folder")

    requests.get('http://' + getSparkIp() + ':5000/clearKML')

    return HttpResponse(status=204)


def settingsIndex(request):
    settings = Setting.objects.all()
    return render(request, 'floybd/settings/settings.html', {'settings': settings})


def openHelp(request):
    refererPage = request.META.get('HTTP_REFERER')
    splittedUrl = refererPage.split("/")
    refererUrl = splittedUrl[len(splittedUrl)-1]
    print(refererUrl)
    return JsonResponse({'currentPage': refererUrl})


def weatherDemos(request):
    return render(request, 'floybd/weather/currentWeatherTour.html')


def demoEarthquakes(request):
    return render(request, 'floybd/earthquakes/demoEarthquakes.html')


def stopTourView(request):
    stopTour()
    return HttpResponse(status=204)


def launchScreenSaver(request):
    stopTour()
    command = "echo '' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    command = "sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " './bin/screensaver.py \"./bin/tour.sh ./bin/queries.txt\"'"
    os.system(command)

    return HttpResponse(status=204)


def stopScreenSaver(request):

    command = "sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " 'pkill screensaver.py '"
    os.system(command)

    return HttpResponse(status=204)


def clearLGCache(request):
    command = "sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " 'rm -r /home/lg/.googleearth/Cache/* '"
    os.system(command)
    return HttpResponse(status=204)


def relaunchLG(request):
    command = "sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " './bin/lg-relaunch '"
    os.system(command)
    return HttpResponse(status=204)


@csrf_exempt
@require_POST
def webhook(request):
    request_data = json.loads(request.body)
    action = request_data['result']['action']
    return JsonResponse("")
