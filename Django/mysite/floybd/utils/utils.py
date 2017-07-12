import socket
from ..models import Setting


def getDjangoIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def getLGIp():
    settingObject = Setting.objects.get(key="lgIp")
    return settingObject.value


def getSparkIp():
    settingObject = Setting.objects.get(key="sparkIp")
    return settingObject.value


def getLGPass():
    settingObject = Setting.objects.get(key="LGPassword")
    return settingObject.value


def backspace(n):
    print('\r' * n, end='')


def printpercentage(value):
    s = str(value) + '%'
    print("%.2f" % float(value), "%", end='')
    backspace(len(s))
