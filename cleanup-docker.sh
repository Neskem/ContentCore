#!/bin/bash -x

#docker stop article-dev redis postgresql nginx
docker stop article-dev redis nginx article-beat-dev
#docker rm article-dev redis postgresql nginx
docker rm article-dev redis nginx article-beat-dev
docker network rm dev-net
