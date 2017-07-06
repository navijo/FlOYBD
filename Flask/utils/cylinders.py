import simplekml
import json
from polycircles import polycircles
import time
from subprocess import call

class CylindersKml(object):

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.kml_var = simplekml.Kml()

    def makeKML(self):
        current_milli_time = int(round(time.time()))
        self.parseData()
        self.saveKml(current_milli_time)
        #self.sendKml(current_milli_time)

    def makeKMZ(self):
        current_milli_time = int(round(time.time()))
        self.parseData()
        self.saveKmz(current_milli_time)
        #self.sendKml(current_milli_time)

    def parseData(self):
        for element in self.data:
            if(not element['description'][0]==None and not element['description'][1]==None  and not element['description'][2]==None):
                self.newCylinder(element['name'], element['description'], element['coordinates'], element['extra'])
                self.newPointer(element['name'], element['description'], element['coordinates'], element['extra'])

    def newPointer(self, name, description, coordinates, extra):
        pointer_max = self.kml_var.newpoint(name=str(description[0])+ u'\u2103')
        pointer_med = self.kml_var.newpoint(name=str(description[1])+ u'\u2103')
        pointer_min = self.kml_var.newpoint(name=str(description[2])+ u'\u2103')
        self.generatePointer(pointer_max, description[0], coordinates, 'max')
        self.generatePointer(pointer_med, description[1], coordinates, 'med')
        self.generatePointer(pointer_min, description[2], coordinates, 'min')

        if extra:
            print ('There is extra !')

    def generatePointer(self, point, temp, coordinates, flag):
        point.altitudemode = 'relativeToGround'
        point.gxballoonvisibility = 0
        point.style.iconstyle.scale = 0
        point.style.labelstyle.scale = 1
        point.style.balloonstyle.displaymode = 'hide'
        if flag == 'min':
            point.style.labelstyle.color = simplekml.Color.lightblue
            point.coords = [(float(coordinates['lng'])-0.025, float(coordinates['lat'])-0.025, 2200*int(temp))]
        elif flag == 'med':
            point.style.labelstyle.color = simplekml.Color.green
            point.coords = [(float(coordinates['lng']), float(coordinates['lat']), 2200*int(temp))]
        elif flag == 'max':
            point.style.labelstyle.color = simplekml.Color.red
            point.coords = [(float(coordinates['lng'])+0.025, float(coordinates['lat'])+0.025, 2200*int(temp))]

    def newCylinder(self, name, description, coordinates, extra):
        shape_polycircle_max = self.kml_var.newmultigeometry(name=name+'-max')
        shape_polycircle_med = self.kml_var.newmultigeometry(name=name+'-med')
        shape_polycircle_min = self.kml_var.newmultigeometry(name=name+'-min')
        self.generateCylinder(shape_polycircle_max, description[0], coordinates, 'max')
        self.generateCylinder(shape_polycircle_med, description[0], coordinates, 'med')
        self.generateCylinder(shape_polycircle_min, description[1], coordinates, 'min')

        if extra:
            print ('There is extra !')

    def generateCylinder(self, shape, temp, coordinates, flag):
        if flag == 'min':
            polycircle = polycircles.Polycircle(latitude=float(coordinates['lat'])-0.025,
            longitude=float(coordinates['lng'])-0.025, radius=1000, number_of_vertices=100)
        elif flag == 'med':
            polycircle = polycircles.Polycircle(latitude=float(coordinates['lat']),
            longitude=float(coordinates['lng']), radius=1000, number_of_vertices=100)
        elif flag == 'max':
            polycircle = polycircles.Polycircle(latitude=float(coordinates['lat'])+0.025,
            longitude=float(coordinates['lng'])+0.025, radius=1000, number_of_vertices=100)

        latloncircle = polycircle.to_lon_lat()
        latlonaltcircle = []
        polygon_circle = []

        multiplier = 2000
        temperature = int(temp)

        # 'Pal' cap a dalt i cercle al final del pal (a dalt de tot)
        for element in latloncircle:
            tup = (element[0], element[1], (temperature * multiplier) + 10,)
            latlonaltcircle.append(tup)

        # Cilindre (interior / exterior)
        for element in latloncircle:
            tup = (element[0], element[1], temperature * multiplier,)
            latlonaltcircle.append(tup)
            tup = (element[0], element[1], 0,)
            latlonaltcircle.append(tup)

        # Un altre cilindre (interior / exterior ?)
        for element in latloncircle:
            tup = (element[0], element[1], 0,)
            latlonaltcircle.append(tup)
            tup = (element[0], element[1], temperature * multiplier,)
            latlonaltcircle.append(tup)

        for element in latloncircle:
            tup = (element[0], element[1], 0,)
            latlonaltcircle.append(tup)

        pol = shape.newpolygon()
        pol.outerboundaryis = latlonaltcircle

        pol.altitudemode = simplekml.AltitudeMode.relativetoground
        pol.extrude = 5
        pol.style.linestyle.width = 5000

        polygon_circle.append(polycircle)

        latlonaltcircle = []

        # Cyrcle (tapadera del cilindre) de dalt de tot (interior i exterior)
        for element in latloncircle:
            tup = (element[0], element[1], (temperature * multiplier) + 20,)
            latlonaltcircle.append(tup)

        pol = shape.newpolygon()
        pol.outerboundaryis = latlonaltcircle

        pol.altitudemode = simplekml.AltitudeMode.relativetoground
        pol.extrude = 5
        self.addColor(pol, flag)

        pol.style.linestyle.width = 5000

        polygon_circle.append(polycircle)

    def addColor(self, polygon, flag):
        if flag == 'min':
            polygon.style.polystyle.color = simplekml.Color.blue
            polygon.style.linestyle.color = simplekml.Color.blue
        elif flag =='med':
            polygon.style.polystyle.color = simplekml.Color.green
            polygon.style.linestyle.color = simplekml.Color.green
        elif flag =='max':
            polygon.style.polystyle.color = simplekml.Color.red
            polygon.style.linestyle.color = simplekml.Color.red
 
    def saveKml(self,current_milli_time):
        self.kml_var.save("./kmls/" + self.name+".kml")

    def saveKmz(self,current_milli_time):
        self.kml_var.savekmz("./kmls/" + self.name+".kmz", format=False)

    def sendKml(self,current_milli_time):
        command = "sshpass -p 'lqgalaxy' echo 'http://130.206.117.178:8000/cylinders_weather.kml' | ssh lg@192.168.88.242 'cat - > /var/www/html/kmls.txt'"
        call([command])
        


'''
https://github.com/LiquidGalaxyLAB/ViewYourData/blob/master/VYD_Project/VYD/Utils/PresentationManager/cylinder_generator.py
https://developers.google.com/maps/documentation/geocoding/intro?hl=es-419
'''
