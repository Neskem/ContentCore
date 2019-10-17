#!/bin/bash

rm -rf ./mercury-parser
curl -sL https://deb.nodesource.com/setup_10.x | bash -
apt-get install nodejs
apt-get -r install git
git clone https://github.com/postlight/mercury-parser.git
# shellcheck disable=SC2164
cd ./mercury-parser
npm install

