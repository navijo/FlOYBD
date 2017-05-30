#!/bin/bash

source ~/GSOC17/FlOYBD/virtualEnv/bin/activate
python gatherAndInsert.py -t day -y 2017 > cronLog.txt &
