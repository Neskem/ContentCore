#!/bin/bash -x

# MAC OS need to install this command to use realpath: brew install coreutils
curDir=$(dirname "$(realpath $0)")

# Create self docker network
docker network create dev-net

# Create postgresql container and restore sample data
# docker run --net=dev-net --name postgresql -e POSTGRES_PASSWORD=breaktime -d -p 5432:5432 postgres:9.5
# sleep 5

# MAC OS need to download postgresql APP from postgres offical website.
# PGPASSWORD=breaktime /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h localhost < break-article/data/postgresql/init.sql
PGPASSWORD=admin /Applications/Postgres.app/Contents/Versions/10/bin/psql -U postgres -h 35.194.207.202 < break-article/data/postgresql/init.sql

# Create redis server
docker run --net=dev-net --name redis -d redis:4.0

# Start the dev container, and mapping source code folder from hosted server.
docker run --net=dev-net --name article-dev -d -v $curDir/break-article/breakarticle:/opt/breaktime/breakarticle break-article-dev
docker exec -it article-dev python3 /opt/breaktime/initdb.py

# Start nginx and forword request to break-article uwsgi:8700
docker run --net=dev-net --name nginx -d -p 80:80 nginx:1.10.3-alpine
# docker run --net=dev-net --name nginx -d -p 8080:80 nginx:1.10.3-alpine
docker cp break-article/data/nginx/nginx.conf nginx:/etc/nginx
docker cp break-article/data/nginx/conf.d/breaktime-article.conf nginx:/etc/nginx/conf.d/default.conf
docker restart nginx

