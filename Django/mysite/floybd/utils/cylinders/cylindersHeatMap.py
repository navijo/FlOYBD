import simplekml
import json
from polycircles import polycircles
import time
from subprocess import call

class CylindersKmlHeatmap(object):

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.kml_var = simplekml.Kml()

    def makeKML(self, dirPath2):
        self.parseData()
        print("Saving kml into " + dirPath2)
        self.saveKml(dirPath2)

    def parseData(self):
        counter = 1
        for element in self.data:
            print("Parsing #"+str(counter)+":\t"+str(element))
            if float(abs(element[2])) <= 0:
                continue
            self.newCylinder(str(counter), element[2], (element[0], element[1]))
            counter += 1

    def newCylinder(self, name, description, coordinates):
        shape_polycircle = self.kml_var.newmultigeometry(name=name)

        self.generateCylinder(shape_polycircle, description, coordinates, description)

    def generateCylinder(self, shape, magnitude, coordinates, flag):

        polycircle = polycircles.Polycircle(latitude=float(coordinates[0]),
        longitude=float(coordinates[1]), radius=float(abs(magnitude))*10000, number_of_vertices=36)

        pol = self.kml_var.newpolygon(name=str(magnitude), description=str(magnitude),
                                      outerboundaryis=polycircle.to_kml())

        #latloncircle = polycircle.to_lon_lat()
        #latlonaltcircle = []
        #polygon_circle = []

        #multiplier = 8000
        #magnitude = int(abs(magnitude))

        # 'Pal' cap a dalt i cercle al final del pal (a dalt de tot)
        #for element in latloncircle:
        #   tup = (element[0], element[1], (magnitude * multiplier) + 10,)
        #   latlonaltcircle.append(tup)

        # Cilindre (interior / exterior)
        #for element in latloncircle:
        #   tup = (element[0], element[1], magnitude * multiplier,)
        #   latlonaltcircle.append(tup)
        #   tup = (element[0], element[1], 0,)
        #   latlonaltcircle.append(tup)

        # Un altre cilindre (interior / exterior ?)
        #for element in latloncircle:
        #   tup = (element[0], element[1], 0,)
        #   latlonaltcircle.append(tup)
        #   tup = (element[0], element[1], magnitude * multiplier,)
        #   latlonaltcircle.append(tup)

        #        for element in latloncircle:
        #   tup = (element[0], element[1], 0,)
        #   latlonaltcircle.append(tup)

        #pol = shape.newpolygon()
        #pol.outerboundaryis = latlonaltcircle

        #pol.altitudemode = simplekml.AltitudeMode.relativetoground
        #pol.extrude = 5
        #pol.style.linestyle.width = 5000

        #polygon_circle.append(polycircle)

        #latlonaltcircle = []

        # Cyrcle (tapadera del cilindre) de dalt de tot (interior i exterior)
        #for element in latloncircle:
        #    tup = (element[0], element[1], (magnitude * multiplier) + 20,)
        #   latlonaltcircle.append(tup)

        #pol = shape.newpolygon()
        #pol.outerboundaryis = latlonaltcircle

        pol.altitudemode = simplekml.AltitudeMode.relativetoground
        pol.extrude = 1
        self.addColor(pol, flag)

        pol.style.linestyle.width = 5000

        #polygon_circle.append(polycircle)


    def addColor(self, polygon, flag):
        absMagnitude = abs(float(flag))
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

