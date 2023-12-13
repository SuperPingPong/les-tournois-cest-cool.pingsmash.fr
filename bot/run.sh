#!/bin/bash

CONTAINER_NAME=les-tournois-cest-coolpingsmashfr_bot

docker build --no-cache -t $CONTAINER_NAME .
#  docker build -t $CONTAINER_NAME .
docker rm -f $CONTAINER_NAME 2>/dev/null
docker run -d --name $CONTAINER_NAME $CONTAINER_NAME 

