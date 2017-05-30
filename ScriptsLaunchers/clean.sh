#!/bin/bash
source cronEnv.sh
python cleanAndInsert.py > cleanLog.txt &

