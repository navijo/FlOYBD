
from django.shortcuts import render
from ..forms import UploadFileForm

import simplekml

import os
import tarfile
import zipfile
import time
from ..utils import *
from .GTFSUtils import *
from ..gtfs_models import Agency

def uploadGTFS(request):
    if request.method == 'POST':
        title = request.POST['title']
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            millis = int(round(time.time() * 1000))
            form.title = title
            handle_uploaded_file(request.FILES['file'], form.title, millis)
            #kmlPath = handle_uploaded_file(request.FILES['file'], form.title, millis)
            #return render(request, 'floybd/gtfs/viewGTFS.html', {'form': form,'kml':kmlPath})
            agencies = Agency.objects.all()
            return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})
    else:
        form = UploadFileForm()
        return render(request, 'floybd/indexGTFS.html', {'form': form})


def handle_uploaded_file(f, title, millis):
    ip = getIp()
    if not os.path.exists("static/upload/gtfs"):
        print("Creating upload/gtfs folder")
        os.makedirs("static/upload/gtfs")

    extension = get_extension(f)
    print("Extension:" + str(extension))
    if extension not in [".zip", ".tar", ".tgz"]:
        print("Saving normal File")
        saveNormalFile(f, title, extension)
    else:
        saveNormalFile(f, title, extension)
        decompressFile(f, title, extension)
        parseGTFS(title)

    # kmlwriter.py google_transit.zip googleTest.kml
    #zipName = title+extension
    #kmlName = title+"_"+str(millis)+".kml"
    #kmlPath = "http://"+ip+":8000/static/kmls/" + kmlName

    #command = "python2 static/utils/gtfs/kmlwriter.py static/upload/gtfs/"+zipName+" static/kmls/"+kmlName
    #os.system(command)
    #return kmlPath


def parseGTFS(title):

    parseAgency("static/upload/gtfs/"+title)
    parseCalendar("static/upload/gtfs/"+title)
    parseStops("static/upload/gtfs/" + title)
    parseRoutes("static/upload/gtfs/" + title)
    parseTrips("static/upload/gtfs/" + title)
    parseStopTimes("static/upload/gtfs/" + title)




def get_extension(file):
    name, extension = os.path.splitext(file.name)
    return extension


def saveNormalFile(file, title, extension):
    with open('static/upload/gtfs/' + title + extension, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def decompressFile(file, title, extension):
    print("Decompressing..."+extension)
    if str(extension) == str('.zip'):
        print("Is Zip")
        opener, mode = zipfile.ZipFile, 'r'
    elif str(extension) == str('.tar.gz') or str(extension) == str('.tgz'):
        print("Is GZ")
        opener, mode = tarfile.open, 'r:gz'
    elif str(extension) == str('.tar.bz2') or str(extension) == str('.tbz'):
        print("Is Tar")
        opener, mode = tarfile.open, 'r:bz2'
    else:
        raise (ValueError, "Could not extract `%s` as no appropriate extractor is found" % file)

    cwd = os.getcwd()

    if not os.path.exists("static/upload/gtfs/"+title):
        os.makedirs("static/upload/gtfs/"+title)

    os.chdir("static/upload/gtfs/"+title)

    try:
        compressedFile = opener(file, mode)
        try:
            compressedFile.extractall()
        finally:
            compressedFile.close()
    finally:
        os.chdir(cwd)


def sendGTFSToLG(request):
    kmlPath = request.POST["kmlPath"]
    form = UploadFileForm()

    command = "echo '" + kmlPath + "' | sshpass -p lqgalaxy ssh lg@192.168.88.198 'cat - > /var/www/html/kmls.txt'"
    os.system(command)

    return render(request, 'floybd/gtfs/viewGTFS.html', {'form': form, 'kml': kmlPath})


def uploadgtfs(request):
    print("Upload GTFS")
    form = UploadFileForm()
    return render(request, 'floybd/gtfs/gtfsUpload.html', {'form': form})


def viewgtfs(request):
    print("View GTFS")
    agencies = Agency.objects.all()
    return render(request, 'floybd/gtfs/viewGTFSAgencies.html', {'agencies': agencies})


def getAgenciesAndGenerateKML(request):
    agencies = request.POST.getlist('agenciesSelected')
    gtfsKml = simplekml.Kml()
    stops_folder = gtfsKml.newfolder(name='Stops')
    routes_folder = gtfsKml.newfolder(name='Routes')
    for selectedAgency in agencies:
        agency = Agency.objects.get(agency_id=selectedAgency)
        #getRoutesForAgency
        routes = Route.objects.filter(agency_id=agency.agency_id)
        for route in routes:
            print("Route:" + str(route.route_long_name))
            # getTripForRoute
            trips = Trip.objects.filter(route_id=route.route_id)
            for trip in trips:
                #getCalendarForTrip
                calendar = Calendar.objects.filter(service_id=trip.service_id)
                #getCalendarInfo
                # getStopTimesForTrip
                stop_times = Stop_time.objects.filter(trip_id=trip.trip_id)
                for stop_time in stop_times:
                    stops = Stop.objects.filter(stop_id=stop_time.stop_id)
                    for stop in stops:
                        stops_folder.newpoint(name=stop.name, description=stop.stop_desc,
                                              coords=[(stop.stop_lon, stop.stop_lat)])

    kmlPath = "static/kmls/gtfs.kml"
    gtfsKml.save(kmlPath)

    return kmlPath
