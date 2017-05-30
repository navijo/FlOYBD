#!/bin/bash
source cronEnv.sh
#source /home/ubuntu/Downloads/spark/spark-2.0.2/conf/spark-env.sh
#source /home/ubuntu/TFM/dataMiningEnv/bin/activate
#env > env.output
#cd /home/ubuntu/TFM/cassandraScripts/goodOne
#nohup stdbuf -oL python cleanAndInsert.py > nohupClean.out &
python cleanAndInsert.py > cleanLog.txt &

