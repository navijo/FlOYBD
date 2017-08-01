import pandas as pd
from ..models import Agency
from ..models import Calendar
from ..models import Route
from ..models import Stop
from ..models import Stop_time
from ..models import Trip
from ..models import Calendar_date

from datetime import datetime
from django.db.utils import IntegrityError
import traceback
import numpy as np
from django.contrib.contenttypes.models import ContentType

from math import sin, cos, sqrt, atan2, radians
from geopy.distance import great_circle

import logging
logger = logging.getLogger("django")


def getDistanceBetweenPoints(point1Lat, point1Lon, point2Lat, point2Lon):
    point1 = (point1Lat, point1Lon)
    point2 = (point2Lat, point2Lon)
    return great_circle(point1, point2).kilometers


def getDistanceBetweenPoints1(point1Lat, point1Lon, point2Lat, point3Lon):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(point1Lat)
    lon1 = radians(point1Lon)
    lat2 = radians(point2Lat)
    lon2 = radians(point3Lon)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    if distance == 0:
        logger.info("#####", point1Lat, ",", point1Lon, ",", point2Lat, ",", point3Lon)

    return distance


def parseAgency(basePath):
    logger.info("Processing Agencies")
    data = pd.read_csv(basePath+'/agency.txt', engine='python')
    for index, row in data.iterrows():
        try:
            agency = Agency()
            agency.agency_id = row['agency_id']
            agency.agency_url = row['agency_url']
            agency.agency_name = row['agency_name']
            agency.agency_timezone = row['agency_timezone']
            agency.save()
        except IntegrityError:
            logger.error("Agency Error: ", row['agency_name'])
            pass


def parseCalendar(basePath):
    logger.info("Processing Calendar")
    data = pd.read_csv(basePath+'/calendar.txt', engine='python')
    for index, row in data.iterrows():
        calendar = Calendar()
        calendar.service_id = row['service_id']
        startDate = datetime.strptime(str(row['start_date']), '%Y%m%d')

        calendar.start_date = startDate
        endDate = datetime.strptime(str(row['end_date']), '%Y%m%d')

        calendar.end_date = endDate
        calendar.monday = row['monday']
        calendar.tuesday = row['tuesday']
        calendar.wednesday = row['wednesday']
        calendar.thursday = row['thursday']
        calendar.friday = row['friday']
        calendar.saturday = row['saturday']
        calendar.sunday = row['sunday']
        calendar.save()


def parseCalendarDates(basepath):
    logger.info("Processing Calendar Dates")

    data = pd.read_csv(basepath + '/calendar_dates.txt', engine='python')
    for index, row in data.iterrows():
        calendar_date = Calendar_date()
        calendar_date.service_id = row['service_id']

        date = datetime.strptime(str(row['date']), '%Y%m%d')
        calendar_date.date = date

        calendar_date.exception_type = int(row['exception_type'])

        calendar_date.save()


def parseRoutes(basePath):
    logger.info("Processing Routes")
    data = pd.read_csv(basePath + '/routes.txt', engine='python')
    for index, row in data.iterrows():
        try:
            route = Route()
            route.route_type = row['route_type']
            route.route_id = row['route_id']
            route.route_short_name = row['route_short_name']
            route.route_long_name = row['route_long_name']
            if 'agency_id' in data.columns and row['agency_id'] is not None:
                agency = Agency.objects.get(agency_id=str(row['agency_id']))
                route.agency = agency
                route.save()
            else:
                logger.debug("Agency Id not found")
                continue
        except Agency.DoesNotExist:
            logger.error("Agency not exist " + str(row['agency_id']))
            continue


def parseStops(basePath):
    logger.info("Processing Stops")
    data = pd.read_csv(basePath + '/stops.txt', engine='python')
    for index, row in data.iterrows():
        stop = Stop()
        stop.stop_lon = row['stop_lon']
        stop.stop_name = row['stop_name']
        stop.stop_lat = row['stop_lat']
        stop.stop_id = row['stop_id']
        if 'location_type' in data.columns:
            stop.location_type = row['location_type']
        stop.save()


def parseStopTimes(basePath):
    logger.info("Processing Stop Times")
    data = pd.read_csv(basePath + '/stop_times.txt', engine='python')
    for index, row in data.iterrows():
        try:
            stop_times = Stop_time()
            trip = Trip.objects.get(trip_id=row['trip_id'])
            if trip is None:
                logger.error("No Existent Trip" + str(row['trip_id']))
                continue
            stop_times.trip = trip

            arrivalTime = datetime.strptime(str(row['arrival_time']), '%H:%M:%S')
            stop_times.arrival_time = arrivalTime

            departuretime = datetime.strptime(str(row['departure_time']), '%H:%M:%S')
            stop_times.departure_time = departuretime

            stop = Stop.objects.get(stop_id=row['stop_id'])
            if stop is None:
                logger.error("No Existent Stop" + str(row['stop_id']))
                continue
            stop_times.stop = stop

            if 'stop_sequence' in data.columns and row['stop_sequence'] is not None \
                    and not np.isnan(row['stop_sequence']):
                stop_times.stop_sequence = row['stop_sequence']
            if 'stop_headsign' in data.columns and row['stop_headsign'] is not None:
                stop_times.stop_headsign = row['stop_headsign']
            if 'pickup_type' in data.columns and row['pickup_type'] is not None \
                    and not np.isnan(row['pickup_type']):
                stop_times.pickup_type = row['pickup_type']
            if 'drop_off_type' in data.columns and row['drop_off_type'] is not None \
                    and not np.isnan(row['drop_off_type']):
                stop_times.drop_off_type = row['drop_off_type']
            if 'shape_dist_traveled' in data.columns and row['shape_dist_traveled'] is not None \
                    and not np.isnan(row['shape_dist_traveled']):
                stop_times.shape_dist_traveled = row['shape_dist_traveled']
            if 'timepoint' in data.columns and row['timepoint'] is not None \
                    and not np.isnan(row['timepoint']):
                stop_times.timepoint = row['timepoint']

            stop_times.save()
        except (ValueError, TypeError) as e:
            logger.error(index, e)
            traceback.print_exc()


def parseTrips(basePath):
    logger.info("Processing Trips")
    data = pd.read_csv(basePath + '/trips.txt', engine='python')
    for index, row in data.iterrows():
        try:
            route = Route.objects.get(route_id=row['route_id'])
            calendar_type = ContentType.objects.get(app_label='floybd', model='calendar')
            calendar = calendar_type.get_object_for_this_type(service_id=row['service_id'])

            trip = Trip(
                route=route,
                trip_id=row['trip_id'],
                trip_headsign=row['trip_headsign'],
                content_object=ContentType.objects.get_for_model(calendar),
                service_id=calendar.service_id
            ).save()

        except Calendar.DoesNotExist:
            logger.error("Calendar not exist " + str(row['service_id']))
            route = Route.objects.get(route_id=row['route_id'])

            calendar_dates = Calendar_date.objects.filter(service_id=row['service_id'])
            calendar_date = calendar_dates.first()
            trip = Trip(
                route=route,
                trip_id=row['trip_id'],
                trip_headsign=row['trip_headsign'],
                content_object=ContentType.objects.get_for_model(calendar_date),
                service_id=calendar_date.service_id
            ).save()

            continue
