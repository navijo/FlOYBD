import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine import connection
from datetime import datetime
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.models import Model


class Agency(Model):
    uid                = columns.UUID(primary_key=True,required=True)
    agency_url         = columns.DateTime(required=False)
    agency_name        = columns.Text(required=True)
    agency_timezone    = columns.Text(required=False)



class Calendar(Model):
    service_id		= columns.Text(primary_key=True)
    start_date		= columns.DateTime(index=True,required=True)
    end_date		= columns.DateTime(index=True,required=True)
    monday		    = columns.Text(required=False)
    tuesday		    = columns.Text(required=False)
    wednesday		= columns.Text(required=False)
    thursday		= columns.Text(required=False)
    friday          = columns.Text(required=False)
    saturday        = columns.Text(required=False)
    sunday          = columns.Text(required=False)



class Calendar_dates(Model):
    service_id      = columns.Text(primary_key=True)
    date            = columns.DateTime(required=False)
    exception_type  = columns.Text(required=False)



class Routes(Model):
    route_id           = columns.Text(primary_key=True)
    route_type         = columns.Text(required=False)
    route_short_name   = columns.Text(required=False)
    route_long_name    = columns.Text(required=False)
    agency_id          = columns.Text(required=True)


class Stops(Model):
    stop_id        = columns.Text(primary_key=True)
    stop_name      = columns.Text(required=False)
    stop_lon       = columns.Decimal(required=True)
    stop_lat       = columns.Decimal(required=True)
    location_type  = columns.Text(required=False)

class Stop_times(Model):
    uid                  = columns.UUID(primary_key=True,required=True)
    trip_id              = columns.Text(required=True)
    arrival_time         = columns.DateTime(required=True)
    departure_time       = columns.DateTime(required=True)
    stop_id              = columns.Text(required=True)
    stop_sequence        = columns.Text(required=False)
    stop_headsign        = columns.Text(required=False)
    pickup_type          = columns.Text(required=False)
    drop_off_type        = columns.Text(required=False)
    shape_dist_traveled  = columns.Text(required=False)

class trips(Model):
    trip_id       = columns.Text(primary_key=True)
    route_id      = columns.Text(required=True)
    service_id    = columns.Text(required=True)
    trip_headsign = columns.Text(required=False)
    

connection.setup(['127.0.0.1','192.168.246.236'], "gtfs", protocol_version=3)

#Create CQL tables
sync_table(Agency)
sync_table(Calendar)
sync_table(Calendar_dates)
sync_table(Routes)
sync_table(Stops)
sync_table(Stop_times)
sync_table(trips)
