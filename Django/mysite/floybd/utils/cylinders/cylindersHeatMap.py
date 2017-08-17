import simplekml
import datetime
from polycircles import polycircles


class CylindersKmlHeatmap(object):

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.kml_var = simplekml.Kml()

    def makeKML(self, dirPath2):
        self.parseData()
        print("Saving kml into " + dirPath2)
        self.saveKml(dirPath2)

    def makeKMZ(self, dirPath2):
        self.parseData()
        print("Saving kmz into " + dirPath2)
        self.saveKmz(dirPath2)

    def parseData(self):
        counter = 1
        for element in self.data:
            if float(abs(element[2])) <= 0:
                continue
            self.newCylinder(element[3], element[4], (element[0], element[1]), element[2])
            counter += 1

    def newCylinder(self, name, description, coordinates, magnitude):
        self.generateCylinder(name, description, coordinates, magnitude)

    def generateCylinder(self, name, description, coordinates, magnitude):
        fechaStr = datetime.datetime.fromtimestamp(int(description) / 1000).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        polycircle = polycircles.Polycircle(latitude=float(coordinates[0]),
                                            longitude=float(coordinates[1]),
                                            radius=float(abs(magnitude))*20000, number_of_vertices=36)

        pol = self.kml_var.newpolygon(name=name, description=str(fechaStr),
                                      outerboundaryis=polycircle.to_kml())

        pol.altitudemode = simplekml.AltitudeMode.relativetoground
        pol.extrude = 1
        pol.style.polystyle.fill = 1
        self.addColor(pol, magnitude)

        pol.style.linestyle.width = 5000

    def addColor(self, polygon, magnitude):
        absMagnitude = abs(float(magnitude))
        if absMagnitude <= 2:
            polygon.style.polystyle.color = "1e00FF14"
            polygon.style.linestyle.color = "1e00FF14"
        elif 2 < absMagnitude <= 5:
            polygon.style.polystyle.color = "1e1478FF"
            polygon.style.linestyle.color = "1e1478FF"
        elif absMagnitude > 5:
            polygon.style.polystyle.color = "1e1400FF"
            polygon.style.linestyle.color = "1e1400FF"

    def saveKml(self, path):
        self.kml_var.save(path)

    def saveKmz(self, path):
        self.kml_var.savekmz(path, format=False)
