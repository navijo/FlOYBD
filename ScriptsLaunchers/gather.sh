#!/bin/bash

#source ~/GSOC17/FlOYBD/virtualEnv/bin/activate
source cronEnv.sh
cd ~/GSOC17/FlOYBD/DataGatheringAndCleaning
python gatherAndInsertWeather.py -t day -y 2017 > gatherLog.txt &
