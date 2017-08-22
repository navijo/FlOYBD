#!/bin/sh

SERVICE="ultrahook"
RESULT=`ps -a | sed -n /${SERVICE}/p`

while :
do
	if [ "${RESULT:-null}" = null ]; then
    	echo "Ultrahook not running"
		ultrahook liquidgalaxylab http://0.0.0.0:5000 &
		echo "Ultrahook started"
	else
	    echo "ultrahook running"
	fi
    sleep 30
done
