FROM            python:3.6
MAINTAINER BreakTime Inc.

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN \
    pip install -r requirements.txt && \
    pip install --upgrade google-cloud-logging && \
    mkdir -p /var/log/contentcore/ && \
    echo Done

COPY . /usr/src/app
COPY    entrypoint.sh /
RUN     chmod +x /entrypoint.sh
