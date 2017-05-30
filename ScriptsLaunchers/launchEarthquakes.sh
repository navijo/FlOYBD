#!/bin/bash

source ~/GSOC17/FlOYBD/virtualEnv/bin/activate
python earthquakes.py > cronLog.txt &
