#!/bin/bash
source ~/FlOYBD/virtualEnv/bin/activate
cd ~/FlOYBD/Django/mysite/
python manage.py getCurrentWeather
python manage.py getLastWeekEarthquakes
python manage.py getLastWeekEarthquakesHeatMap
