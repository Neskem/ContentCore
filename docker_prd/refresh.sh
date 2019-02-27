#!/bin/bash

# psql client wasn't installed on psql
# refresh the db in postgresql
# PGPASSWORD=ContentBreak_psql1qaz psql -U postgres -h 192.168.18.123 < postgresql/init.sql

docker-compose down -v
# docker-compose won't automatically pull when image already exists
docker-compose pull
# don't build image in prd env
# docker build -t cc -f ../Dockerfile ../
docker-compose up -d
# manual garbage collection
docker rmi $(docker images -f "dangling=true" -q)

docker-compose restart nginx
# check status
docker-compose ps

# check server return status code
curl -v -X GET 'http://localhost:80/v1/create_tasks/1'
