docker-compose stop nginx
docker-compose kill nginx
docker rm nginx
docker rmi $(docker images nginx -q)

docker-compose pull nginx
docker-compose restart nginx

# check status
docker-compose ps

# check server return status code
curl -v -X GET 'http://localhost:80/v1/create_tasks/1'

# c52220624f25
