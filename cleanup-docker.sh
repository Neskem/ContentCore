#!/bin/bash -x

#docker stop article-dev redis postgresql nginx
docker stop article-dev redis nginx
#docker rm article-dev redis postgresql nginx
docker rm article-dev redis nginx
docker network rm dev-net
