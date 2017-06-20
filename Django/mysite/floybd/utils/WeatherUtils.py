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
    maxTemp = calculatedData["max_temp"]
    minTemp = calculatedData["min_temp"]
    temps = [maxTemp, minTemp]

    finalData = {"name": name, "description": temps, "coordinates": coordinates, "extra": ""}
    return finalData
