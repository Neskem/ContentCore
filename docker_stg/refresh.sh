#!/bin/bash


docker-compose down -v

# psql client wasn't installed on psql
# refresh the db in postgresql
PGPASSWORD=admin psql -U postgres -h 10.140.0.16 < postgresql/init.sql

# docker-compose won't automatically pull when image already exists
docker-compose pull
# don't build image in prd env
# docker build -t cc -f ../Dockerfile ../
docker-compose up -d
# manual garbage collection
docker rmi $(docker images -f "dangling=true" -q)

# check status
docker-compose ps
