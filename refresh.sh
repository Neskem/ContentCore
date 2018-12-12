#!/bin/bash

PGPASSWORD=admin psql -U postgres -h 192.168.18.111 < docker/postgresql/init.sql

docker build -t breakcontent -f Dockerfile .

cd docker/
docker-compose stop
docker-compose rm
docker-compose up -d

