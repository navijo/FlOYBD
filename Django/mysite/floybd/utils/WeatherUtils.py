import json

def prepareJson(weatherData, stationData):
    stationData = json.loads(stationData)

    latitude = stationData["latitude"]
    longitude = stationData["longitude"]

    coordinates = {}
    coordinates["lat"] = latitude
    coordinates["lng"] = longitude
    name = stationData["name"]
    coordinatesStr = json.dumps(coordinates)

    calculatedData = json.loads(weatherData)
    #print(calculatedData)
    maxTemp = calculatedData["max_temp"]
    minTemp = calculatedData["min_temp"]
    temps = []
    temps.append(maxTemp)
    temps.append(minTemp)

    finalData = {}
    finalData["name"] = name
    finalData["description"] = temps
    finalData["coordinates"] = coordinates
    finalData["extra"] = ""
    return finalData