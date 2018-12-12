## How to build your development environment

### Prerequisite

* Please install new Ubuntu server. (16.04 or 18.04 will be encouraged)
* Setup your Github key to clone the project breaktime-content and this repository.
* Login server and continue the following steps.

### Installation

Get this repository
```sh
$ git clone <GitHub_Dev_repo>
$ cd BreakTime_Dev
```

The script will install necessary packages and docker. After installation, please logout the system and reconnect to server again.
```sh
$ sudo ./pre-install.sh
$ logout
```

Start to build up development environment
```sh
$ ./build-docker-images.sh
```

After compete the image build, you can easy start the docker development.
```sh
$ ./start-docker.sh
```

This may take few minutes to complete then you can see the docker containers running in the background.

```sh
$ docker ps -a
CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                           NAMES
4dbbd78e5965        nginx:1.10.3-alpine   "nginx -g 'daemon of…"   31 minutes ago      Up 31 minutes       443/tcp, 0.0.0.0:80->80/tcp   nginx
2b95ab84045b        content-dev       "/docker-entrypoint.…"   31 minutes ago      Up 31 minutes       8700/tcp                        content-dev
48e7f8408883        redis:4.0             "docker-entrypoint.s…"   31 minutes ago      Up 31 minutes       6379/tcp                        redis
```

The source folder under breaktime-content-dev/break-content/breakcontent will be mounted as a docker volume on /opt/breaktime/breakcontent. Which means you can directly change your code outside the docker and running your code inside the docker environment. Thus, you don't need to install development tools into containers. You can also commit your code directly. If you want to cleanup and re-start all docker containers, please execute with:
```sh
$ ./cleanup-docker.sh
$ ./start-docker.sh
```
Then you will get clean development docker containers again.

### Usage

You can access data directly via psql to GCP environment 35.194.207.202:5432 and default password is "admin".
```sh
$ "/Applications/Postgres.app/Contents/Versions/10/bin/psql" -p5432 -Upostgres -h 35.194.207.202
```

Entering content container via the command:
```sh
$ docker exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it content-dev /bin/bash
or
$ docker exec -it content-dev /bin/bash
```

You may also access the content API directly to 127.0.0.1:80
```sh
$ curl -X POST 'http://localhost:80/v0/hips/dpi/callback2' -H 'Cache-Control: no-cache' -H 'Content-Type: application/json' -d 'API testing'
{"data":{},"message":"OK"}
```
