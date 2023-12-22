#!/bin/bash

# Add git checkout
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi $(docker images -aq) 
docker system prune -a -f
# Remove all volumes, Except for mpbackend_postrgres-data as it contains the database
docker volume rm mpbackend_static
docker volume rm mpbackend_mpbackend

docker-compose -f ../docker-compose.yml -f ../docker-compose.prod.yml up
docker-compose -f ../docker-compose.yml -f ../docker-compose.prod.yml start
