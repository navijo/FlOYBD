from django.shortcuts import render
import shutil
from .utils.lgUtils import *
from .utils.utils import *
import requests
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.http import require_POST
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


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
    helpContent = getHelpContent(refererUrl)
    return JsonResponse({'currentPage': refererUrl, 'helpContent': helpContent})


def weatherDemos(request):
    return render(request, 'floybd/weather/currentWeatherTour.html')


@csrf_exempt
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

    '''command = "sshpass -p lqgalaxy ssh lg@" + getLGIp() + \
              " './bin/screensaver.py \"./bin/tour.sh ./bin/queriesWorldRotation.txt\"'"
    '''

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
    responseStr = request.body
    obj = json.loads(responseStr.decode('utf-8'))
    tourType = obj["result"]["parameters"]["tourType"]
    print(tourType)
    answer = create_webhook_answer("Playing tour " + tourType)
    if tourType == str("weather"):
        sendDemoKmlToLG("dummyWeather.kmz", request)
        time.sleep(3)
        playTour("Tour Current Weather")
    elif tourType == str("latest earthquakes"):
        sendDemoKmlToLG("lastWeekEarthquakes.kmz", request)
        time.sleep(10)
        playTour("LastWeekEarthquakesTour")
    elif tourType == str("heatmap"):
        sendDemoKmlToLG("lastWeekEarthquakesHeatMap.kmz", request)
        time.sleep(5)
        sendFlyToToLG(36.778259, -119.417931, 14500000, 0, 0, 14500000, 2)
    elif tourType == str("gtfs") or tourType == str("transit"):
        millis = int(round(time.time() * 1000))
        command = "echo 'http://" + getDjangoIp() + ":" + getDjangoPort(request) + \
                  "/static/demos/lines_demo.kml?a=" + str(millis) + \
                  "\nhttp://" + getDjangoIp() + ":" + getDjangoPort(request) + \
                  "/static/demos/car_demo.kmz?a=" + str(millis) + \
                  "' | sshpass -p lqgalaxy ssh lg@" + getLGIp() + " 'cat - > /var/www/html/kmls.txt'"
        os.system(command)
        time.sleep(5)
        playTour("GTFSTour")
    elif tourType == str("screensaver"):
        launchScreenSaver(request)
    return JsonResponse(answer)


def create_webhook_answer(answer):
    return {
        "speech": answer,
        "displayText": answer,
        "source": "API.AI-test-simple-Quiz"
    }


def getSlideImage(request):
    currentDir = os.getcwd()
    dirName = "static/img/slides"
    dir1 = os.path.join(currentDir, dirName)
    images = []
    for f in os.listdir(dir1):
        if f.endswith("jpg") or f.endswith("png") or f.endswith("gif"):
            images.append("%s%s/%s" % (settings.MEDIA_URL, dirName, f))
    return JsonResponse({'images': images})


def getHelpContent(refererUrl):
    content = ""
    if refererUrl == "":
        content = "<p>You're on the main screen.<br/>Select some option from the left menu  to interact " \
                  " the application.<br/>" \
                  "<i style=\"font-size:96px;\" class=\"material-icons\">keyboard_arrow_left</i></p>"
    elif refererUrl == "weatherDemos":
        content = "<p>You're on the demo weather screen.<br/>Select some button to launch the corresponding demo " \
                  "tour in Liquid Galaxy or stop the currently playing one.</p>"
    elif refererUrl == "dayWeather":
        content = "<p>Through this screen you can ask for the weather in a concrete day.</br>" \
                  "Select a date and a station from the combo, or check the checkbox if you want the data for all " \
                  "the stations and press the button \"Get Values\"</p>"
    elif refererUrl == "getConcreteDateValues":
        content = "<p>If there are results of your query, they are displayed inside the map.</br>" \
                  "Click on any marker to open the information window </br> or </br>" \
                  "click the  \"Generate Cylinders and send values to LG\" to display" \
                  " a representation of the temperatures in Liquid Galaxy." \
                  "</br> If you want to go back, press the \"Back\" button</p>"
    elif refererUrl == "predictWeather":
        content = "<p>In this screen you can select the values that you want to predict for the desired station.</br>" \
                  "Once you have configured them press the button \"Predict Values\"</p>"
    elif refererUrl == "getPrediction" or refererUrl == "sendPredictionsToLG":
        content = "<p>If there are results of your query, they are displayed inside the map.</br>" \
                  "Click on the marker to open the information window </br> or </br>" \
                  "click the  \"Send values to LG\" to display" \
                  " them in Liquid Galaxy." \
                  "</br> If you want to go back, press the \"Back\" button</p>"
    elif refererUrl == "predictWeatherStats":
        content = "<p>Through this screen you can ask for a weather prediction based on statistical " \
                  "data for one station and the current day.</br>" \
                  "Select a station from the combo and stations and press the button \"Predict Values\"</p>"
    elif refererUrl == "weatherStats":
        content = "<p>Through this screen you can ask for statistical data for one or all stations.</br></br>" \
                  "If you want to get stats calculated from all the data, you have to select the " \
                  "\"Get Stats All Time\" checkbox. If not, you can select the date interval through the " \
                  "corresponding fields.</br></br>If you select \"Get Stats All Time\" checkbox you can also" \
                  " select the option \"Add Graphs to balloon\" that will add a pre-generated graph " \
                  "image to the information balloon associated to each station.</br></br>" \
                  " After these configurations, you can select a concrete stations or " \
                  " mark the corresponding \"Get All Stations\" checkbox to calculate stats for all of them.</br>" \
                  "</br>When all the configuration has been done, by pressing the button \"Get Values\", the desired " \
                  "stats will be calculated."
    elif refererUrl == "citydashboard":
        content = "<p>In this screen you can configure the graphical summary for station going back the desired " \
                  "number of days.</br>" \
                  " You can select the station and the days backward that you want to take into account." \
                  " Once you have configured them press the button \"View Dashboard\".</br></br>" \
                  " Once the graph are generated, you can go over them with your mouse to view the different data" \
                  " points as well as create windows over the data by drawing a rectangle on the small graphs " \
                  " located under each graph.</br>" \
                  " To reset the graphs to its original status, press the button \"Reset Charts\"</p>"
    elif refererUrl == "demoEarthquakes":
        content = "<p>You're on the demo earthquakes screen.<br/>Select some button to launch the corresponding demo " \
                  "tour in Liquid Galaxy or stop the currently playing one.</p>"
    elif refererUrl == "earthquakes":
        content = "<p>Through this screen you can ask for seismological data for a world region.</br></br>" \
                  "First of all, you have to configure the date since you want to get the data.</br></br>" \
                  "Then, by selecting the hand icon over the map, you can navigate through it. When you are on" \
                  "the zone you want, you have to select the square icon and draw a square of the zone that you want" \
                  "to get the data.</br></br> By pressing \"Delete Selected Shaped\" button you can reset " \
                  "your square.</br></br>" \
                  "If you want, you can create a tour (it will only be visible in Liquid Galaxy) through all the " \
                  "earthquakes by selecting the \"Create a tour through all earthquakes\" checkbox.</br></br>" \
                  " By selecting the \"Approximate with Lat/Lon Quadrants \" checkbox," \
                  " the system will use cached data" \
                  "in order to speed up the query.</br></br>" \
                  " Once you have configured your desired parameter, you must press the \"Get Earthquakes\" button" \
                  " Take into account that, depending on your parameters, the process could take some time." \
                  "<p>If there are results of your query, they are displayed inside the map.</br>" \
                  "Click on any circle to open the information window related to each earthquakes </br>" \
                  " The circles are colored depending on its magnitude." \
                  " Green for lower magnitude and red for higher." \
                  "</br> Click the  \"Send values to LG\" to display them in Liquid Galaxy." \
                  "</br> If you want to go back, press the \"Back\" button</p>"
    elif refererUrl == "heatMapEarthquakes":
        content = "<p>Through this screen you can generate a worldwide seismological heatmap.</br></br>" \
                  "You only have to configure the date since you want to get the data and press the " \
                  "\"Get HeatMap\" button.</br>" \
                  " Take into account that, depending on the temporal distance of your date, " \
                  "the process could take some time." \
                  "<p>If there are results of your query, they are displayed inside the map.</br>" \
                  "</br> Click the  \"Send HeatMap KML to LG\" to display the heatmap." \
                  "</br> If you want to go back, press the \"Back\" button</p>"
    elif refererUrl == "demogtfsindex":
        content = "<p>You're on the demo GTFS screen.<br/>Select some button to launch the corresponding demo " \
                  " in Liquid Galaxy or stop the currently playing one.</p>"
    elif refererUrl == "uploadgtfs":
        content = "<p>Through this screen you can upload a compressed file that follows the GTFS " \
                  "specifications.</br></br>" \
                  "You only have to select it from your system, name it and press the \"Upload\" button"
    elif refererUrl == "viewgtfs":
        content = "<p>Through this screen you can configure a GTFS demo visualization </br></br>" \
                  "You only have to select the agency from which you want to simulate its trips data and set a number" \
                  " of simulated trips.</br><i>You can use the search field to filter the table</i></br>" \
                  " Once you have done it, you can press the \"Get Values\" button to generate" \
                  " the simulation.</p>" \
                  "<p>Once the simulation has been done, it will be displayed inside the map.</br>" \
                  "</br> Click the  \"Send Values to LG\" to start the tour on Liquid Galaxy." \
                  "</br> It will launch the number of cars that you had specified alongside the Agency routes" \
                  "</br>If you want to go back, press the \"Back\" button</p>"

    return content
