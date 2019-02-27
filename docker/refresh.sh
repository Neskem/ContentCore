#!/bin/bash

# refresh the db in postgresql
# PGPASSWORD=admin psql -U postgres -h 192.168.18.111 < docker/postgresql/init.sql

docker-compose down -v

PGPASSWORD=admin psql -U postgres -h 35.194.207.202 < postgresql/init.sql

# docker rmi $(docker images nginx -q)

docker build -t cc -f ../Dockerfile ../

docker-compose up -d

# manual garbage collection
docker rmi $(docker images -f "dangling=true" -q)

# for python wsgi.py shell use
cat breakcontent.env | grep -v '^#' | grep -v '^$' | awk '{print "export "$0}'

docker-compose restart nginx

# check status
docker-compose ps

# check server return status code
curl -v -X GET 'http://localhost:80/v1/create_tasks/1'
# check files in container
# docker exec -it web ls -al
# copy & paste manually
