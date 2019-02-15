#!/bin/bash

# refresh the db in postgresql
# PGPASSWORD=admin psql -U postgres -h 192.168.18.111 < docker/postgresql/init.sql
PGPASSWORD=ContentBreak_psql1qaz psql -U postgres -h 192.168.18.123 < postgresql/init.sql

docker-compose down -v

docker build -t cc -f ../Dockerfile ../

docker-compose up -d

# for python wsgi.py shell use
cat breakcontent.env | grep -v '^#' | grep -v '^$' | awk '{print "export "$0}'

# copy & paste manually
