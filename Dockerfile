
FROM            python:3.6
MAINTAINER BreakTime Inc. <lance@breaktime.com.tw>

RUN \
  apt-get update ; \
  apt-get -y install build-essential && \
  apt-get -y install libmysqlclient-dev && \

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

COPY    entrypoint.sh /
RUN     chmod +x /entrypoint.sh
