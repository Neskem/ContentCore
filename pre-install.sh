#!/bin/bash

#apt-get install -y docker.io
#usermod -aG docker $SUDO_USER
#apt install -y postgresql-client-common postgresql-client

docker pull ubuntu:18.04
docker pull postgres:9.5
docker pull redis:4.0
docker pull nginx:1.10.3-alpine

