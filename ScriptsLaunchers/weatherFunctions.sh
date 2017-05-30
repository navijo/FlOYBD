#!/bin/bash

source cronEnv.sh
cd ~/GSOC17/FlOYBD/DataMining/weather
nohup stdbuf -oL python weatherFunctions.py  > functionLogs.out &


