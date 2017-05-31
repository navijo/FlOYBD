#!/bin/bash

source ~/GSOC17/FlOYBD/virtualEnv/bin/activate
cd ~/GSOC17/FlOYBD/DataGatheringAndCleaning
python gatherEarthquakes.py > cronLog.txt &
