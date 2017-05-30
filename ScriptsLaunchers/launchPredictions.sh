#!/bin/bash

#source ~/TFM/dataMiningEnv/bin/activate
source cronEnv.sh
cd ~/TFM/dataminingScripts/weather/ml
nohup stdbuf -oL python linearRegression.py  > linearRegression.out &


