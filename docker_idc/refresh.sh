#!/bin/bash

dropdb=$1
echo "dropdb param: $dropdb"

mkdir -p /tmp/contentcore
docker-compose down -v
# docker-compose build ## When use local cc image, and need to execute this command.

if [ "${dropdb}" = 'drop' ]; then
    sleep 5 # takes time for containter be ready
    if [ -e "/etc/os-release" ]; then
        PGPASSWORD=ContentBreak_psql1qaz psql -h 192.168.250.125 -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
        PGPASSWORD=ContentBreak_psql1qaz psql -h 192.168.250.125 -U postgres -c 'DROP DATABASE break_content'
        sleep 3
        PGPASSWORD=ContentBreak_psql1qaz psql -h 192.168.250.125 -U postgres -c 'CREATE DATABASE break_content'
    else
        PGPASSWORD=ContentBreak_psql1qaz /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 192.168.250.125 -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
        PGPASSWORD=ContentBreak_psql1qaz /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 192.168.250.125 -c 'DROP DATABASE break_content'
        sleep 3
        PGPASSWORD=ContentBreak_psql1qaz /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 192.168.250.125 -c 'CREATE DATABASE break_content'
    fi
fi

docker-compose up -d
sleep 8
docker-compose restart
