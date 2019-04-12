FROM            python:3.6
MAINTAINER BreakTime Inc. <lance@breaktime.com.tw>

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt
RUN pip install --upgrade google-cloud-logging

# maybe not all are necessary
COPY . /usr/src/app

COPY    entrypoint.sh /
RUN     chmod +x /entrypoint.sh
