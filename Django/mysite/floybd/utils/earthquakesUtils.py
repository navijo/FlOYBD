import json

def getYQuadrant(latitude):
    y = 0
    if 60 <= latitude < 80:
        y = 1
    elif 40 <= latitude < 60:
        y = 2
    elif 20 <= latitude < 40:
        y = 3
    elif 0 <= latitude < 20:
        y = 4
    elif -20 <= latitude < 0:
        y = 5
    elif -40 <= latitude < -20:
        y = 6
    elif -60 <= latitude < -40:
        y = 7
    elif -80 <= latitude < -60:
        y = 8
    elif latitude < -80:
        y = 8
    elif 80 <= latitude:
        y = 1
    return y


def getXQuadrant(longitude):
    x = 0
    if 0 <= longitude < 30:
        x = 1
    elif 30 <= longitude < 60:
        x = 2
    elif 60 <= longitude < 90:
        x = 3
    elif 90 <= longitude < 120:
        x = 4
    elif 120 <= longitude < 150:
        x = 5
    elif 150 <= longitude <= 180:
        x = 6
    elif -180 <= longitude < -150:
        x = 7
    elif -150 <= longitude < -120:
        x = 8
    elif -120 <= longitude < -90:
        x = 9
    elif -90 <= longitude < -60:
        x = 10
    elif -60 <= longitude < -30:
        x = 11
    elif -30 <= longitude < 0:
        x = 12
    return x


def replaceJsonString(string):
    replacedString = string.replace("': '", '": "').replace("{'", '{"').replace("', '", '", "')\
        .replace(", '", ', "').replace("'}", '"}').replace(", '", ', "')\
        .replace("':", '":').replace("None", '""')
    jsonString = json.loads(replacedString)
    return jsonString
