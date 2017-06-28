import os
from .utils import *


def sendKmlToLG(fileName):

    command = "echo 'http://" + getDjangoIp() + ":8000/static/kmls/" + fileName + \
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
            + "<gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode>" \
            + "<gx:duration>"+str(duration)+"</gx:duration>" \
            + "</LookAt>"

    command = "echo '" + flyTo + "' | sshpass -p "+getLGPass()+" ssh lg@" + getLGIp() + " 'cat - > /tmp/query.txt'"
    os.system(command)


def playTour(tourName):
    command = "echo 'playtour="+tourName+"' | sshpass -p "+getLGPass()+" ssh lg@" + getLGIp() + \
              " 'cat - > /tmp/query.txt'"
    os.system(command)
