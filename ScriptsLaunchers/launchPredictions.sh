#!/bin/bash

source cronEnv.sh
cd ~/GSOC17/FlOYBD/DataMining/weather/ml
nohup stdbuf -oL python linearRegression.py  > linearRegression.out &


