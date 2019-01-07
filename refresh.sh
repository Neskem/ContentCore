#!/bin/bash

# refresh the db in postgresql
PGPASSWORD=admin psql -U postgres -h 192.168.18.111 < docker/postgresql/init.sql

docker build -t cc -f Dockerfile .

cd docker/
docker-compose down -v
docker-compose up -d

# for python wsgi.py shell
cat breakcontent.env | grep -v '^#' | grep -v '^$' | awk '{print "export "$0}'

# copy & paste manually
