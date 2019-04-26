#!/bin/bash

dropdb=$1
echo "dropdb param: $dropdb"
mkdir -p /tmp/contentcore

docker-compose down -v
# docker-compose build
if [ "$dropdb" == "drop" ]; then
    if [ -e "/etc/os-release" ]; then
        # create external volumn
        # docker volume create --name=pgdata
        psql -h 34.80.84.182 -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
        psql -h 34.80.84.182 -U postgres -c 'DROP DATABASE break_content'
        psql -h 34.80.84.182 -U postgres -c 'CREATE DATABASE break_content'
    else
        PGPASSWORD=admin /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 34.80.84.182 -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
        PGPASSWORD=admin /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 34.80.84.182 -c 'DROP DATABASE break_content'
        PGPASSWORD=admin /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 34.80.84.182 -c 'CREATE DATABASE break_content'
    fi
fi
docker-compose up -d
docker rmi $(docker images -f "dangling=true" -q)
docker-compose ps
