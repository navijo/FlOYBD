#!/bin/bash

source ~/TFM/dataMiningEnv/bin/activate
python gatherAndInsert.py -t day -y 2017 > cronLog.txt &
