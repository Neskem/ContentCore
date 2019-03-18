#!/bin/bash
# PGPASSWORD=admin psql -U postgres -h 192.168.18.111 < docker/postgresql/init.sql
docker-compose down -v
docker build -t cc -f ../Dockerfile ../
docker-compose up -d
# manual garbage collection
docker rmi $(docker images -f "dangling=true" -q)
# cat breakcontent.env | grep -v '^#' | grep -v '^$' | awk '{print "export "$0}'
# docker-compose restart nginx
psql -U postgres -h localhost < postgresql/init.sql
# docker-compose restart
docker-compose ps
curl -v -X GET 'http://localhost:8100/v1/create_tasks/1'
# check files in container
# docker exec -it web ls -al
# copy & paste manually
