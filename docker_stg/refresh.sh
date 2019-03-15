#!/bin/bash

docker-compose down -v

docker build -t cc -f ../Dockerfile ../

docker-compose up -d

docker rmi $(docker images -f "dangling=true" -q)

# PGPASSWORD=admin psql -U postgres -h 192.168.18.111 < docker/postgresql/init.sql

docker-compose ps

# check server return status code
curl -v -X GET 'http://localhost:80/v1/create_tasks/1'

