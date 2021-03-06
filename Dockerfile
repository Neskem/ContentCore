FROM ubuntu:18.04
MAINTAINER BreakTime Inc.

ARG DEBIAN_FRONTEND=noninteractive
ENV TERM linux

RUN \
  apt-get update && apt-get install --assume-yes apt-utils ; \
  apt-get -y install git curl python3 python3-dev python3-setuptools python3-pip && \
  apt-get -y install python python-dev python-setuptools python-pip && \
  apt-get -y install build-essential libffi-dev && \
  apt-get -y install libpq-dev vim && \
  apt-get -y install libmysqlclient-dev && \
  apt-get -y install wget software-properties-common

RUN \
  curl -sL https://deb.nodesource.com/setup_10.x | bash - ; \
  apt-get install nodejs

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN \
    pip install supervisor==3.2 && \
    pip3 install -r requirements.txt && \
    # pip install --upgrade google-cloud-logging && \
    mkdir -p /var/log/contentcore/ /etc/supervisor/conf.d /etc/breaktime && \
    echo Done

COPY . /usr/src/app
COPY    entrypoint.sh /
COPY supervisord.conf /etc/
COPY supervisor-uwsgi.conf supervisor-worker.conf /etc/supervisor/conf.d/

ENV BREAKTIME_CONTENT_SETTINGS_PATH=/etc/breaktime/breakcontent.conf

RUN python3 compile.py build_ext --inplace
RUN ./build-cython.sh
RUN chmod +x /entrypoint.sh
