#!/bin/bash

# refresh the db in postgresql
PGPASSWORD=admin psql -U postgres -h 192.168.18.111 < docker/postgresql/init.sql

#docker build -t breakcontent -f Dockerfile .

cd docker/
docker-compose down -v
docker-compose up -d

