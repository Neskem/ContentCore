# Pull base image.
FROM ubuntu:18.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TERM linux

# system prepare
RUN \
  apt-get update ; \
  apt-get -y install git python3 python3-dev python3-setuptools python3-pip && \
  apt-get -y install python python-dev python-setuptools python-pip && \
  apt-get -y install build-essential libffi-dev && \
  apt-get -y install libpq-dev vim && \
  apt-get -y install libmysqlclient-dev && \
  apt-get -y install wget software-properties-common && \
  mkdir -p /opt/breaktime /var/log/breaktime /etc/breaktime/ssl

COPY ["breaktime-content.conf", "/etc/breaktime/breaktime-content.conf"]
COPY ["uwsgi.ini", "requirements.txt", "wsgi.py", "manage.py", "/opt/breaktime/"]

RUN \
  pip3 install uwsgi && \
  pip3 install -r /opt/breaktime/requirements.txt && \
  echo Done


COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
WORKDIR /opt/breaktime

