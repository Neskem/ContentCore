#!/bin/bash

# psql client wasn't installed on psql
# refresh the db in postgresql
PASSWORD=ContentBreak_psql1qaz psql -U postgres -h 10.140.15.248 < postgresql/init.sql

docker-compose down -v
# docker-compose won't automatically pull when image already exists
docker-compose pull
# don't build image in prd env
docker-compose up -d
# manual garbage collection
docker rmi $(docker images -f "dangling=true" -q)

docker-compose ps

curl -v -X GET 'http://localhost:80/v1/create_tasks/1'

