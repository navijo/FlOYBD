#!/bin/bash

function ultrahookF {
    ultrahook liquidgalaxylab http://0.0.0.0:8000
}

until ultrahookF; do
echo "ultrahook server failed"
sleep 2
done
