#!/bin/bash

dropdb=$1
echo "dropdb $dropdb"
docker-compose down -v
docker-compose build
# create external volumn
docker-compose up -d
docker rmi $(docker images -f "dangling=true" -q)
if [ "$dropdb" == "drop" ]; then
    docker volume create --name=data
    # ------------------ START init DB ------------------
    psql -h localhost -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
    psql -h localhost -U postgres -c 'DROP DATABASE break_content'
    psql -h localhost -U postgres -c 'CREATE DATABASE break_content'
    # ------------------ END ------------------
else
    psql -h localhost -U postgres -c 'CREATE DATABASE break_content'
fi

docker-compose ps
curl -v -X GET 'http://localhost:8100/v1/create_tasks/1'

