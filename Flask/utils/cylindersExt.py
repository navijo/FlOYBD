import simplekml
from polycircles import polycircles
import time
from subprocess import call


class CylindersKmlExtended(object):

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.kml_var = simplekml.Kml()

    def makeKML(self):
        current_milli_time = int(round(time.time()))
        self.parseData()
        self.saveKml(current_milli_time)

    def makeKMLWithTourAndRotation(self):
        current_milli_time = int(round(time.time()))
        self.parseData()
        self.tourAndRotation()
        self.saveKml(current_milli_time)

    def makeKMZ(self):
        current_milli_time = int(round(time.time()))
        self.parseData()
        self.saveKmz(current_milli_time)
    
    def makeKMZWithTourAndRotation(self):
        current_milli_time = int(round(time.time()))
        self.parseData()
        self.tourAndRotation()
        self.saveKmz(current_milli_time)
    
    def parseData(self):
        for element in self.data:
            for innerElement in element:
                if not innerElement['description'][0]==None and not innerElement['description'][1]==None and not innerElement['description'][2]==None:
                    self.newCylinder(innerElement['name'], innerElement['description'], innerElement['coordinates'], innerElement['extra'])
                    self.newPointer(innerElement['name'], innerElement['description'], innerElement['coordinates'], innerElement['extra'])

    def tourAndRotation(self):
        tourAndRotation = self.kml_var.newgxtour(name="Tour And Rotation")
        playlistTourAndRotation = tourAndRotation.newgxplaylist()
        for element in self.data:
            for innerElement in element:
                if not innerElement['description'][0]==None and not innerElement['description'][1]==None and not innerElement['description'][2]==None:
                    self.newFlyTo(playlistTourAndRotation, innerElement['coordinates'])
                    self.newRotation(playlistTourAndRotation, innerElement['coordinates'])

    def newFlyTo(self, playlist,coordinates):
        flyto = playlist.newgxflyto(gxduration=4.0)
        flyto.gxflytomode = "smooth"
        flyto.altitudemode = simplekml.AltitudeMode.relativetoground
            
        flyto.lookat.gxaltitudemode = simplekml.GxAltitudeMode.relativetoseafloor
        flyto.lookat.longitude = float(coordinates['lng'])
        flyto.lookat.latitude = float(coordinates['lat'])
        flyto.lookat.altitude = 25000
        flyto.lookat.range = 130000
        flyto.lookat.heading = 0
        flyto.lookat.tilt = 77
        playlist.newgxwait(gxduration=4.0)

    def newRotation(self, playlist,coordinates):
        for angle in range(0, 360, 10):
            flyto = playlist.newgxflyto(gxduration=1.0)
            flyto.gxflytomode = "smooth"
            flyto.altitudemode = simplekml.AltitudeMode.relativetoground
            
            flyto.lookat.gxaltitudemode = simplekml.GxAltitudeMode.relativetoseafloor
            flyto.lookat.latitude = float(coordinates['lat'])
            flyto.lookat.longitude = float(coordinates['lng'])
            flyto.lookat.altitude = 25000
            flyto.lookat.range = 130000
            flyto.lookat.heading = angle
            flyto.lookat.tilt = 77

    def newPointer(self, name, description, coordinates, extra):
        pointer_max = self.kml_var.newpoint(name=str(description[0])+ u'\u2103')
        pointer_med = self.kml_var.newpoint(name=str(description[1])+ u'\u2103')
        pointer_min = self.kml_var.newpoint(name=str(description[2])+ u'\u2103')
        self.generatePointer(pointer_max, description[0], coordinates, 'max')
        self.generatePointer(pointer_med, description[1], coordinates, 'med')
        self.generatePointer(pointer_min, description[2], coordinates, 'min')

        if extra:
            print('There is extra !')

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
        self.generateCylinder(shape_polycircle_med, description[1], coordinates, 'med')
        self.generateCylinder(shape_polycircle_min, description[2], coordinates, 'min')

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

        for element in latloncircle:
            tup = (element[0], element[1], (temperature * multiplier) + 10,)
            latlonaltcircle.append(tup)

        for element in latloncircle:
            tup = (element[0], element[1], temperature * multiplier,)
            latlonaltcircle.append(tup)
            tup = (element[0], element[1], 0,)
            latlonaltcircle.append(tup)
       
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

        # Topping Circle
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


