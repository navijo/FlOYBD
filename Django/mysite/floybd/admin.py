from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
# Register your models here.
from django.forms import  ModelForm
from django import forms
from django.db import models
from django.http import HttpResponseRedirect
from django.conf.urls import url
import requests
import json
from datetime import datetime

from .models import Station
from .models import ApiKey


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
        timestamp = datetime.strptime(jsonData["valid_until"], "%Y-%m-%d %H:%M:%S").date()
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
