from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


## GTFS Models
class Agency(models.Model):
    agency_id = models.CharField(primary_key=True, blank=False, null=False, max_length=200, unique=True)
    agency_url = models.URLField(blank=False, null=False)
    agency_name = models.CharField(max_length=200, blank=False, null=False)
    agency_timezone = models.CharField(blank=False, null=False, max_length=100)
    agency_lang = models.CharField(blank=True, null=True, max_length=2)
    agency_phone = models.CharField(blank=True, null=True, max_length=12)
    agency_fare_url = models.URLField(blank=True, null=True)
    agency_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return str(self.agency_name)


class Calendar(models.Model):
    service_id = models.CharField(primary_key=True, unique=True, max_length=200)
    monday = models.BooleanField(null=False, blank=False)
    tuesday = models.BooleanField(null=False, blank=False)
    wednesday = models.BooleanField(null=False, blank=False)
    thursday = models.BooleanField(null=False, blank=False)
    friday = models.BooleanField(null=False, blank=False)
    saturday = models.BooleanField(null=False, blank=False)
    sunday = models.BooleanField(null=False, blank=False)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)

    def __str__(self):
        return str(self.service_id)


class Calendar_date(models.Model):
    exception_types = (
        (1, 'Added'),
        (2, 'Removed')
    )
    #auto_increment_id = models.AutoField(primary_key=True,default=0)
    service_id = models.CharField(max_length=200)
    date = models.DateField(null=False, blank=False)
    exception_type = models.IntegerField(choices=exception_types, null=False, blank=False)

    def __str__(self):
        return str(self.service_id+" for " + str(self.date))


class Fare_Attribute(models.Model):
    payment_methods = (
        (0, 'On Board'),
        (1, 'Before Boarding')
    )

    transfers_methods = (
        (0, 'No transfers permitted'),
        (1, 'Passenger may transfer once'),
        (2, 'Passenger may transfer twice')
    )

    fare_id = models.CharField(primary_key=True, unique=True, max_length=200)
    price = models.FloatField(null=False, blank=False)
    currency_type = models.CharField(max_length=3, blank=False, null=False)
    payment_method = models.IntegerField(choices=payment_methods, blank=False, null=False)
    transfers = models.IntegerField(choices=transfers_methods, blank=True, null=True)
    transfer_duration = models.FloatField(blank=True, null=False)

    def __str__(self):
        return str(self.service_id)


class Route(models.Model):
    route_types = (
        (0, 'Tram, Streetcar, Light rail'),
        (1, 'Subway, Metro'),
        (2, 'Rail'),
        (3, 'Bus'),
        (4, 'Ferry'),
        (5, 'Cable Car'),
        (6, 'Gondola, Suspended cable car'),
        (7, 'Funicular')
    )

    route_id = models.CharField(primary_key=True, unique=True, max_length=200)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, null=True, blank=True)
    route_short_name = models.CharField(null=False, blank=False, max_length=200)
    route_long_name = models.CharField(null=False, blank=False, max_length=200)
    route_desc = models.CharField(null=True, blank=True, max_length=200)
    route_type = models.IntegerField(choices=route_types, default=0, null=False,blank=False)
    route_url = models.URLField(blank=True, null=True)
    route_color = models.CharField(blank=True, null=True, max_length=6)
    route_text_color = models.CharField(blank=True, null=True, max_length=6)

    def __str__(self):
        return str(self.route_id+" " + self.route_short_name)

    def GetPatternIdTripDict(self):
        """Return a dictionary that maps pattern_id to a list of Trip objects."""
        d = {}
        trips = Trip.objects.filter(route_id=self.route_id)
        for t in trips:
            d.setdefault(t.pattern_id, []).append(t)
        return d


class Trip(models.Model):
    choices = (
        (0, 'No Information'),
        (1, 'At least one place'),
        (2, 'No Place'))

    direction_choices = (
        (0, 'Outbound'),
        (1, 'Inbound'))

    trip_id = models.CharField(primary_key=True, unique=True, max_length=200)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    dynamic_key = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    service_id = models.CharField(max_length=200)
    content_object = GenericForeignKey('dynamic_key', 'service_id')

    trip_headsign = models.CharField(null=True, blank=True, max_length=200)
    trip_short_name = models.CharField(null=True, blank=True, max_length=200)
    direction_id = models.IntegerField(choices=direction_choices, null=True, blank=True)
    block_id = models.CharField(null=False, blank=False, max_length=200)
    #shape_id = models. TODO!!!!!!!!

    wheelchair_accessible = models.IntegerField(choices=choices, default=0)
    bikes_allowed = models.IntegerField(choices=choices, default=0)

    def __str__(self):
        return str(self.trip_id + " " + self.trip_headsign)


class Stop(models.Model):
    location_choices = (
        (0, 'Stop'),
        (1, 'Station'))

    choices = (
        (0, 'No Information'),
        (1, 'At least one place'),
        (2, 'No Place'))

    stop_id = models.CharField(primary_key=True, unique=True, max_length=200)
    stop_code = models.CharField(null=True, blank=True, max_length=200)
    stop_name = models.CharField(null=False, blank=False, max_length=200)
    stop_desc = models.CharField(null=True, blank=True, max_length=200)
    stop_lat = models.FloatField(null=False, blank=False)
    stop_lon = models.FloatField(null=False, blank=False)
    zone_id = models.CharField(null=True, blank=True, max_length=200)
    stop_url = models.URLField(null=True, blank=True)
    location_type = models.IntegerField(choices=location_choices, blank=True, null=True)
    stop_timezone = models.CharField(null=True, blank=True, max_length=200)
    wheelchair_boarding = models.IntegerField(choices=choices, blank=True, null=True)

    def __str__(self):
        return str(self.stop_id + " " + self.stop_name)


class Stop_time(models.Model):
    pickup_choices = (
        (0, 'Regularly scheduled pickup'),
        (1, 'No pickup available'),
        (2, 'Must phone agency to arrange pickup'),
        (3, 'Must coordinate with driver to arrange pickup'))

    drop_off_choices = (
        (0, 'Regularly scheduled drop off'),
        (1, 'No drop off available'),
        (2, 'Must phone agency to arrange drop off'),
        (3, 'Must coordinate with driver to arrange drop off'))

    times_choices = (
        (0, 'Times are considered approximate'),
        (1, 'Times are considered exact'))

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    arrival_time = models.TimeField(null=False, blank=False, help_text="HH:MM:SS")
    departure_time = models.TimeField(null=False, blank=False, help_text="HH:MM:SS")
    stop = models.ForeignKey(Stop, related_name='stops', on_delete=models.CASCADE)
    stop_sequence = models.PositiveIntegerField(null=True, blank=True)
    stop_headsign = models.CharField(null=True, blank=True, max_length=200)
    pickup_type = models.IntegerField(choices=pickup_choices, blank=True, null=True, default=0)
    drop_off_type = models.IntegerField(choices=drop_off_choices, blank=True, null=True, default=0)
    timepoint = models.IntegerField(choices=times_choices, blank=True, null=True, default=1)

    def __str__(self):
        return str(self.trip_id) + " " + str(self.stop) + " " + str(self.arrival_time)\
               + " " + str(self.departure_time)
