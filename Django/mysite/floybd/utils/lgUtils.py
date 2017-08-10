import os
from .utils import *
import simplekml
import time


def sendDemoKmlToLG(fileName, request):

    millis = int(round(time.time() * 1000))
    command = "echo 'http://" + getDjangoIp() + ":"+getDjangoPort(request)+"/static/demos/" + fileName + "?a=" +\
              str(millis) + \
              "' | sshpass -p "+getLGPass()+" ssh lg@" + getLGIp() + " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)


def sendKmlToLG1(fileName, request):
    millis = int(round(time.time() * 1000))
    command = "echo 'http://" + getDjangoIp() + ":"+getDjangoPort(request)+"/static/kmls/" + fileName + "?a=" +\
              str(millis) + \
              "' | sshpass -p "+getLGPass()+" ssh lg@" + getLGIp() + " 'cat - > /var/www/html/kmls_1.txt'"
    os.system(command)


def sendKmlToLG(fileName, request):
    millis = int(round(time.time() * 1000))
    command = "echo 'http://" + getDjangoIp() + ":"+getDjangoPort(request)+"/static/kmls/" + fileName + "?a=" +\
              str(millis) + \
              "' | sshpass -p "+getLGPass()+" ssh lg@" + getLGIp() + " 'cat - > /var/www/html/kmls.txt'"
    os.system(command)


def sendFlyToToLG(lat, lon, altitude, heading, tilt, pRange, duration):
    flyTo = "flytoview=<LookAt>" \
            + "<longitude>" + str(lon) + "</longitude>" \
            + "<latitude>" + str(lat) + "</latitude>" \
            + "<altitude>"+str(altitude)+"</altitude>" \
            + "<heading>"+str(heading)+"</heading>" \
            + "<tilt>"+str(tilt)+"</tilt>" \
            + "<range>"+str(pRange)+"</range>" \
            + "<altitudeMode>relativeToGround</altitudeMode>" \
            + "<gx:altitudeMode>relativeToGround</gx:altitudeMode>" \
            + "<gx:duration>"+str(duration)+"</gx:duration>" \
            + "</LookAt>"

    command = "echo '" + flyTo + "' | sshpass -p "+getLGPass()+" ssh lg@" + getLGIp() + " 'cat - > /tmp/query.txt'"
    os.system(command)


def playTour(tourName):
    stopTour()
    time.sleep(2)
    command = "echo 'playtour="+tourName+"' | sshpass -p "+getLGPass()+" ssh lg@" + getLGIp() + \
              " 'cat - > /tmp/query.txt'"
    os.system(command)


def stopTour():
    command = "echo 'exittour=true' | sshpass -p "+getLGPass()+" ssh lg@" + getLGIp() + \
              " 'cat - > /tmp/query.txt'"
    os.system(command)


def doFlyTo(playList, latitude, longitude, altitude, pRange, duration, tilt=77):
    flyto = playList.newgxflyto(gxduration=duration)
    flyto.gxflytomode = simplekml.GxFlyToMode.bounce
    flyto.altitudemode = simplekml.AltitudeMode.relativetoground

    flyto.lookat.gxaltitudemode = simplekml.GxAltitudeMode.relativetoseafloor
    flyto.lookat.longitude = float(longitude)
    flyto.lookat.latitude = float(latitude)
    flyto.lookat.altitude = altitude
    flyto.lookat.heading = 0
    flyto.lookat.tilt = tilt
    flyto.lookat.range = pRange


def doFlyToSmooth(playList, latitude, longitude, altitude, pRange, duration, tilt=77):
    flyto = playList.newgxflyto(gxduration=duration)
    flyto.gxflytomode = simplekml.GxFlyToMode.smooth
    flyto.altitudemode = simplekml.AltitudeMode.relativetoground

    flyto.lookat.gxaltitudemode = simplekml.GxAltitudeMode.relativetoseafloor
    flyto.lookat.longitude = float(longitude)
    flyto.lookat.latitude = float(latitude)
    flyto.lookat.altitude = altitude
    flyto.lookat.heading = 0
    flyto.lookat.tilt = tilt
    flyto.lookat.range = pRange


def doRotation(playList, latitude, longitude, altitude, pRange):
    for angle in range(0, 360, 10):
        flyto = playList.newgxflyto(gxduration=1.0)
        flyto.gxflytomode = simplekml.GxFlyToMode.smooth
        flyto.altitudemode = simplekml.AltitudeMode.relativetoground

        flyto.lookat.gxaltitudemode = simplekml.GxAltitudeMode.relativetoseafloor
        flyto.lookat.longitude = float(longitude)
        flyto.lookat.latitude = float(latitude)
        flyto.lookat.altitude = altitude
        flyto.lookat.heading = angle
        flyto.lookat.tilt = 77
        flyto.lookat.range = pRange


