#!/bin/bash

docker-compose down -v
docker-compose build
docker-compose up -d
docker rmi $(docker images -f "dangling=true" -q)
# ------------------ START init DB ------------------
psql -h localhost -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
psql -h localhost -U postgres -c 'DROP DATABASE break_content'
psql -h localhost -U postgres -c 'CREATE DATABASE break_content'
# ------------------ END ------------------
docker-compose ps
curl -v -X GET 'http://localhost:8100/v1/create_tasks/1'

