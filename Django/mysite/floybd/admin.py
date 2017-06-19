from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
# Register your models here.
from django.forms import ModelForm
from django import forms

from django.http import HttpResponseRedirect
from django.conf.urls import url

import json
from datetime import datetime
from django.contrib.admin import widgets

from .models import *


class StationAdmin(admin.ModelAdmin):
    change_list_template = 'admin/floybd/station/change_list.html'
    fieldsets = [
        ('Descriptive', {'fields': ['station_id', 'name', 'province']}),
        ('Location', {'fields': ['latitude', 'longitude', 'altitude']}),
    ]

    def get_urls(self):
        urls = super(StationAdmin, self).get_urls()
        my_urls = [url(r"^importStations/$", import_stations)]
        return my_urls + urls

admin.site.register(Station, StationAdmin)


@staff_member_required
def import_stations(request):
    stations = requests.get('http://130.206.117.178:5000/getAllStations')
    jsonStr = json.loads(stations.text)
    for record in jsonStr:
        station = Station(station_id=record["station_id"],
                          name=record["name"],
                          province=record["province"],
                          latitude=record["latitude"],
                          longitude=record["longitude"],
                          altitude=record["altitude"])
        station.save()
        print(station)
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


class ApiKeyForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ApiKeyForm, self).__init__(*args, **kwargs)
        call = requests.get('http://130.206.117.178:5000/getKey')
        jsonResponse = call.text
        jsonData = json.loads(jsonResponse)
        timestamp = datetime.datetime.strptime(jsonData["valid_until"], "%Y-%m-%d %H:%M:%S").date()
        if not kwargs.get('initial'):
            kwargs['initial'] = {}
        kwargs['initial'].update({'valid_date': timestamp})

    def save(self, commit=True):
        return super(ApiKeyForm, self).save(commit=commit)

    class Meta:
        model = ApiKey
        fields = ['creation_date', 'key', 'valid_date']


class ApiKeyAdmin(admin.ModelAdmin):
    form = ApiKeyForm
    fieldsets = [
        ('Descriptive', {'fields': ['creation_date', 'key', 'valid_date']}),
    ]

admin.site.register(ApiKey, ApiKeyAdmin)


class AgencyAdmin(admin.ModelAdmin):
    class Meta:
        model = Agency
admin.site.register(Agency, AgencyAdmin)


class CalendarForm(ModelForm):
    start_date = forms.DateField(widget=widgets.AdminDateWidget(format='%Y%m%d'))
    end_date = forms.DateField(widget=widgets.AdminDateWidget(format='%Y%m%d'))

    class Meta:
        model = Calendar
        fields = ['service_id', 'monday', 'tuesday', 'wednesday', 'thursday',
                  'friday', 'saturday', 'sunday', 'start_date', 'end_date']


class CalendarAdmin(admin.ModelAdmin):
    form = CalendarForm

admin.site.register(Calendar, CalendarAdmin)


class CalendarDateForm(ModelForm):
    date = forms.DateField(widget=widgets.AdminDateWidget(format='%Y%m%d'))

    class Meta:
        model = Calendar_date
        fields = ['service_id', 'date', 'exception_type']


class CalendarDateAdmin(admin.ModelAdmin):
    form = CalendarDateForm

admin.site.register(Calendar_date, CalendarDateAdmin)


class FareAttributeAdmin(admin.ModelAdmin):
    class Meta:
        model = Fare_Attribute
admin.site.register(Fare_Attribute, FareAttributeAdmin)


class RouteAdmin(admin.ModelAdmin):
    class Meta:
        model = Route
admin.site.register(Route, RouteAdmin)





class StopAdmin(admin.ModelAdmin):
    class Meta:
        model = Stop
admin.site.register(Stop, StopAdmin)


class Stop_timeForm(ModelForm):
    arrival_time = forms.TimeField(widget=widgets.AdminTimeWidget(format='%HH:%MM:%SS'))
    departure_time = forms.TimeField(widget=widgets.AdminTimeWidget(format='%HH:%MM:%SS'))

    class Meta:
        model = Stop_time
        fields = ['trip', 'arrival_time', 'departure_time', 'stop', 'stop_sequence',
                  'stop_headsign', 'pickup_type', 'drop_off_type', 'timepoint']


class Stop_timeAdmin(admin.ModelAdmin):
    form = Stop_timeForm

admin.site.register(Stop_time, Stop_timeAdmin)


class TripForm(ModelForm):

    class Meta:
        model = Trip
        fields = ['trip_id', 'route', 'service_id', 'trip_headsign', 'trip_short_name',
                  'direction_id', 'block_id', 'wheelchair_accessible', 'bikes_allowed']



class TripAdmin(admin.ModelAdmin):
    form = TripForm

admin.site.register(Trip, TripAdmin)


class SettingsForm(ModelForm):

    class Meta:
        model = Setting
        fields = ['key', 'value']

class SettingsAdmin(admin.ModelAdmin):
    form = SettingsForm

admin.site.register(Setting, SettingsAdmin)


