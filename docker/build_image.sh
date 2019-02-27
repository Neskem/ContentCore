
docker-compose down -v

docker build -t cc -f ../Dockerfile ../

docker rmi $(docker images -f "dangling=true" -q)

# pack image
docker save -o /home/lance/playground/cc.tar cc
