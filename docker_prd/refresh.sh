#!/bin/bash

# psql client wasn't installed on psql
# refresh the db in postgresql
# PGPASSWORD=ContentBreak_psql1qaz psql -U postgres -h 192.168.18.123 < postgresql/init.sql

docker-compose down -v
# don't build image in prd env
# docker build -t cc -f ../Dockerfile ../
docker-compose up -d

