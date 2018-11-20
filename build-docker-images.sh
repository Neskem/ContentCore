#!/bin/bash

# MAC OS need to install this command to use realpath: brew install coreutils
curDir=$(dirname "$(realpath $0)")

# Clean-up old image if existed.
for image_name in break-article-dev break-article-base
do
    if [ $(docker images $image_name -q | wc -l) == "1" ]; then
        docker rmi $image_name
        echo "Docker image: $image_name was removed."
    fi
done

# Clone break-article project and dev package into it
cd $curDir
#git clone <GitHub_Source_Code>
cp -R docker-dev/* break-article

# Build base and dev docker images
cd $curDir/break-article
docker build -t break-article-base .
docker build -t break-article-dev -f Dockerfile-dev .

