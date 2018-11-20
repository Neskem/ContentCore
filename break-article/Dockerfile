# Pull base image.
FROM ubuntu:18.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TERM linux

RUN \
  apt-get update ; \
  apt-get -y install git python3 python3-dev python3-setuptools python3-pip && \
  apt-get -y install python python-dev python-setuptools python-pip && \
  apt-get -y install build-essential libffi-dev && \
  apt-get -y install libpq-dev vim && \
  apt-get -y install libmysqlclient-dev && \
  apt-get -y install wget software-properties-common

ADD ["./uwsgi.ini", "./requirements.txt", "/opt/breaktime/"]
COPY ["supervisord.conf", "/etc/"]

# supervisor 3.2 or above is required to pass environment variables
RUN \
  pip install supervisor==3.2 && \
  pip3 install uwsgi && \
  pip3 install -r /opt/breaktime/requirements.txt && \
  mkdir -p /etc/supervisor/conf.d /var/log/breaktime /opt/breaktime /etc/breaktime/ssl && \
  echo Done
 
COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 8700
CMD ["supervisord", "-n"]
VOLUME ["/var/log/breaktime", "/etc/breaktime", "/opt/breaktime"]
WORKDIR /opt/breaktime
ENV BREAKTIME_ARTICLE_SETTINGS_PATH=/etc/breaktime/breaktime-article.conf
