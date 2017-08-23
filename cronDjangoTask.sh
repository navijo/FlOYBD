#!/bin/bash
source virtualEnv/bin/activate
cd Django/mysite/
nohup python manage.py getCurrentWeather &> logCurrentWeatherJob.out &
nohup python manage.py getLastWeekEarthquakes &> loglastWeekEarthquakes.out &
nohup python manage.py getLastWeekEarthquakesHeatMap &> logLastWeekEarthquakesHeatMap.out &
nohup python manage.py demoGTFS &> logDemoGTFS.out &

