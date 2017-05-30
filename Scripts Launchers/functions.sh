#!/bin/bash

source cronEnv.sh
#cd ~/TFM/dataminingScripts/weather
nohup stdbuf -oL python weatherFunctions.py  > functionLogs.out &
#python weatherFunctions.py > functionsLog.txt

