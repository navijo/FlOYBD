from django.db import models
import requests
import datetime
# Create your models here.
from django.utils.encoding import python_2_unicode_compatible
from .gtfs_models import *

@python_2_unicode_compatible
class Station(models.Model):
    station_id = models.CharField(max_length=10)
    name = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()

    def __str__(self):
        return self.name + " ( " +self.province + " ) "

    class Meta:
        #order_with_respect_to = 'name'
        ordering = ['name', 'province']


class ApiKey(models.Model):
    creation_date = models.DateField()
    valid_date = models.DateField(blank=True, null=True)
    key = models.TextField()

    def __str__(self):
        return str(self.creation_date)

    def save(self, *args, **kwargs):
        call = requests.get('http://130.206.117.178:5000/saveAPIKeyGet?key='+str(self.key))
        valid_date = self.creation_date + datetime.timedelta(days=10)
        self.valid_date = valid_date
        super(ApiKey, self).save()

