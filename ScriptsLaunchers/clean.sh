#!/bin/bash
source cronEnv.sh
cd ~/GSOC17/FlOYBD/DataGatheringAndCleaning
python cleanAndInsertWeather.py > cleanLog.txt &

