import xml.etree.ElementTree as ET


def init():
    root = ET.Element('kml')
    root.attrib['xmlns'] = 'http://earth.google.com/kml/2.1'
    doc = ET.SubElement(root, 'Document')
    open_tag = ET.SubElement(doc, 'open')
    open_tag.text = '1'

    return doc


def end(doc, name):
    output = open("static/kmls/"+name+".kml", 'wb')
    output.write(b"""<?xml version="1.0" encoding="UTF-8"?>\n""")
    ET.ElementTree(doc).write(output, 'utf-8')


def CreateFolder(parent, name, visible=True, description=None):
    folder = ET.SubElement(parent, 'Folder')
    name_tag = ET.SubElement(folder, 'name')
    name_tag.text = name
    if description is not None:
        desc_tag = ET.SubElement(folder, 'description')
        desc_tag.text = description
    if not visible:
        visibility = ET.SubElement(folder, 'visibility')
        visibility.text = '0'
    return folder


def StopFolderSelectionMethod(stop_folder):

    # Create the various sub-folders for showing the stop hierarchy
    station_folder = CreateFolder(stop_folder, 'Stations')
    platform_folder = CreateFolder(stop_folder, 'Platforms')
    platform_connections = CreateFolder(platform_folder, 'Connections')
    entrance_folder = CreateFolder(stop_folder, 'Entrances')
    entrance_connections = CreateFolder(entrance_folder, 'Connections')
    standalone_folder = CreateFolder(stop_folder, 'Stand-Alone')

    def FolderSelectionMethod(stop):
        return (standalone_folder, None)
    return FolderSelectionMethod


def SetIndentation(elem, level=0):
    """Indented the ElementTree DOM.

    This is the recommended way to cause an ElementTree DOM to be
    prettyprinted on output, as per: http://effbot.org/zone/element-lib.htm

    Run this on the root element before outputting the tree.

    Args:
      elem: The element to start indenting from, usually the document root.
      level: Current indentation level for recursion.
    """
    i = "\n" + level*"  "
    if len(elem):
      if not elem.text or not elem.text.strip():
        elem.text = i + "  "
      for elem in elem:
        SetIndentation(elem, level+1)
      if not elem.tail or not elem.tail.strip():
        elem.tail = i
    else:
      if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

def CreateStyle(doc, style_id, style_dict):
    def CreateElements(current_element, current_dict):
      for (key, value) in current_dict.items():
        element = ET.SubElement(current_element, key)
        if isinstance(value, dict):
          CreateElements(element, value)
        else:
          element.text = value

    style = ET.SubElement(doc, 'Style', {'id': style_id})
    CreateElements(style, style_dict)
    return style

def StopStyleSelectionMethod(doc):

    CreateStyle(doc, 'stop_standalone', {'IconStyle': {'color': 'ff00ff00'}})

    def StyleSelectionMethod(stop):
      return ('stop_standalone', None)

    return StyleSelectionMethod


def CreatePlacemark(parent, name, style_id=None, visible=True,description=None):

    placemark = ET.SubElement(parent, 'Placemark')
    placemark_name = ET.SubElement(placemark, 'name')
    placemark_name.text = name
    if description is not None:
      desc_tag = ET.SubElement(placemark, 'description')
      desc_tag.text = description
    if style_id is not None:
      styleurl = ET.SubElement(placemark, 'styleUrl')
      styleurl.text = '#%s' % style_id
    if not visible:
      visibility = ET.SubElement(placemark, 'visibility')
      visibility.text = '0'
    return placemark


def CreateStopPlacemark(stop_folder, stop, style_id):
    desc_items = []
    desc_items.append("Stop id: %s" % stop.stop_id)
    if stop.stop_desc:
      desc_items.append(stop.stop_desc)
    if stop.stop_url:
      desc_items.append('Stop info page: <a href="%s">%s</a>' % (
          stop.stop_url, stop.stop_url))
    description = '<br/>'.join(desc_items) or None
    placemark = CreatePlacemark(stop_folder, stop.stop_name,
                                        description=description,
                                        style_id=style_id)
    point = ET.SubElement(placemark, 'Point')
    coordinates = ET.SubElement(point, 'coordinates')
    coordinates.text = '%.6f,%.6f' % (stop.stop_lon, stop.stop_lat)


def CreateStyleForRoute( doc, route):
    style_id = 'route_%s' % route.route_id
    style = ET.SubElement(doc, 'Style', {'id': style_id})
    linestyle = ET.SubElement(style, 'LineStyle')
    width = ET.SubElement(linestyle, 'width')
    type_to_width = {0: '3',  # Tram
                     1: '3',  # Subway
                     2: '5',  # Rail
                     3: '1'}  # Bus
    width.text = type_to_width.get(route.route_type, '1')
    if route.route_color:
      color = ET.SubElement(linestyle, 'color')
      red = route.route_color[0:2].lower()
      green = route.route_color[2:4].lower()
      blue = route.route_color[4:6].lower()
      color.text = 'ff%s%s%s' % (blue, green, red)
    return style_id


def CreateLineString(parent, coordinate_list):

    if not coordinate_list:
      return None
    linestring = ET.SubElement(parent, 'LineString')
    tessellate = ET.SubElement(linestring, 'tessellate')
    tessellate.text = '1'
    if len(coordinate_list[0]) == 3:
      altitude_mode = ET.SubElement(linestring, 'altitudeMode')
      altitude_mode.text = 'absolute'
    coordinates = ET.SubElement(linestring, 'coordinates')
    if len(coordinate_list[0]) == 3:
      coordinate_str_list = ['%f,%f,%f' % t for t in coordinate_list]
    else:
      coordinate_str_list = ['%f,%f' % t for t in coordinate_list]
    coordinates.text = ' '.join(coordinate_str_list)
    return linestring


def CreateRoutePatternsFolder(parent, route, style_id=None, visible=True):
    #trips = Trip.objects.filter(route_id=route.route_id)

    pattern_id_to_trips = route.GetPatternIdTripDict()
    #if not pattern_id_to_trips:
     # return None

    # sort by number of trips using the pattern
    pattern_trips = pattern_id_to_trips.values()
    pattern_trips.sort(lambda a, b: (len(a) > len(b))-(len(a) < len(b)))

    folder = CreateFolder(parent, 'Patterns', visible)
    #for n, trips in enumerate(pattern_trips):
    for n, trips in enumerate(pattern_trips):
      trip_ids = [trip.trip_id for trip in trips]
      name = 'Pattern %d (trips: %d)' % (n+1, len(trips))
      description = 'Trips using this pattern (%d in total): %s' % (
          len(trips), ', '.join(trip_ids))
      placemark = CreatePlacemark(folder, name, style_id, visible,description)
      coordinates = [(stop.stop_lon, stop.stop_lat)
                     for stop in trips[0].GetPattern()]
      CreateLineString(placemark, coordinates)
    return folder



def createStopsFolder(doc, stops):
    stopsFolder = CreateFolder(doc, "Stops")
    stop_folder_selection = StopFolderSelectionMethod(stopsFolder)
    stop_style_selection = StopStyleSelectionMethod(doc)
    for stop in stops:
        (folder, pathway_folder) = stop_folder_selection(stop)
        (style_id, pathway_style_id) = stop_style_selection(stop)
        CreateStopPlacemark(folder, stop, style_id)
    return stopsFolder


def CreateRoutesFolder(doc, routes, route_type=None):

    def GetRouteName(route):
      name_parts = []
      if route.route_short_name:
        name_parts.append('<b>%s</b>' % route.route_short_name)
      if route.route_long_name:
        name_parts.append(route.route_long_name)
      return ' - '.join(name_parts) or route.route_id

    def GetRouteDescription(route):
      desc_items = []
      if route.route_desc:
        desc_items.append(route.route_desc)
      if route.route_url:
        desc_items.append('Route info page: <a href="%s">%s</a>' % (
            route.route_url, route.route_url))
      description = '<br/>'.join(desc_items)
      return description or None

    routes = [route for route in routes
              if route_type is None or route.route_type == route_type]
    if not routes:
      return None
    routes.sort(key=lambda x: GetRouteName(x))

    if route_type is not None:
      route_type_names = {0: 'Tram, Streetcar or Light rail',
                          1: 'Subway or Metro',
                          2: 'Rail',
                          3: 'Bus',
                          4: 'Ferry',
                          5: 'Cable car',
                          6: 'Gondola or suspended cable car',
                          7: 'Funicular'}
      type_name = route_type_names.get(route_type, str(route_type))
      folder_name = 'Routes - %s' % type_name
    else:
      folder_name = 'Routes'
    routes_folder = CreateFolder(doc, folder_name, visible=False)

    for route in routes:
      style_id = CreateStyleForRoute(doc, route)
      route_folder = CreateFolder(routes_folder, GetRouteName(route),
                                        description=GetRouteDescription(route))
      #CreateRouteShapesFolder(route., route_folder, route,style_id, False)
      CreateRoutePatternsFolder(route_folder, route, style_id, False)

    return routes_folder




