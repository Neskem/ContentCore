#!/bin/bash

dropdb=$1
echo "dropdb param: $dropdb"

mkdir -p /tmp/contentcore
docker-compose down -v
# docker-compose build
if [ "$dropdb" == "drop" ]; then
    docker volume rm pgdata
    # create external volumn
    docker volume create --name=pgdata
    docker-compose up -d
    sleep 5 # takes time for containter be ready
    if [ -e "/etc/os-release" ]; then
        # ------------------ START init DB ------------------
        docker exec -it psql psql -h localhost -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
        docker exec -it psql psql -h localhost -U postgres -c 'DROP DATABASE break_content'
        sleep 3
        docker exec -it psql psql -h localhost -U postgres -c 'CREATE DATABASE break_content'
        # ------------------ END ------------------
        # psql -h 34.80.84.182 -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
        # psql -h 34.80.84.182 -U postgres -c 'DROP DATABASE break_content'
        # psql -h 34.80.84.182 -U postgres -c 'CREATE DATABASE break_content'
    else
        docker exec -it psql psql -h localhost -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
        docker exec -it psql psql -h localhost -U postgres -c 'DROP DATABASE break_content'
        sleep 3
        docker exec -it psql psql -h localhost -U postgres -c 'CREATE DATABASE break_content'
        # PGPASSWORD=admin /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 34.80.84.182 -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
        # PGPASSWORD=admin /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 34.80.84.182 -c 'DROP DATABASE break_content'
        # PGPASSWORD=admin /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 34.80.84.182 -c 'CREATE DATABASE break_content'
    fi
fi
docker-compose up -d
docker-compose ps
