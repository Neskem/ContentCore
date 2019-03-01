CC_deploy_procedure

* ssh login
```
# AC
ssh ubuntu@192.168.18.121
# redis
ssh ubuntu@192.168.18.122
# psql
ssh ubuntu@192.168.18.123
```

* always switch to root user if not
```shell
sudo su
```

* prerequisite (suggested)

```shell

sudo apt-get install language-pack-UTF-8

```

# install postgresql

* (ref)[https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04]

* procedure
```shell
sudo apt update
sudo apt install postgresql postgresql-contrib

```

* edit config
```shell
sudo vi /etc/postgresql/10/main/pg_hba.conf

# IPv4 local connections:
#host    all             all             127.0.0.1/32            md5
host    all             all             0.0.0.0/0               md5

# IPv6 local connections:
#host    all             all             ::1/128                 md5
host    all             all             ::/0                    md5

sudo vi /etc/postgresql/10/main/postgresql.conf

listen_addresses = '*'
#ssl = on
ssl = off

```

* procedure
```shell
sudo -i -u postgres
psql
postgres=# alter role postgres with password 'ContentBreak_psql1qaz';

# exit
\q

# try access w/ pw
psql -h localhost -U postgres

# enter pw
ContentBreak_psql1qaz

# create db
CREATE DATABASE break_content;

# restart
service postgresql restart

```


# Install redis

* procedure
```shell
sudo su

apt-get update
sudo apt-get update
sudo apt-get install redis-server
sudo vi /etc/redis/redis.conf

# bind 127.0.0.1 ::1
#protected-mode yes
protected-mode no
# requirepass foobared
requirepass ContentBreak_1qaz

sudo service redis-server restart
```

# Install CC
* procedure
```
sudo su
```

* [install docker](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04)
```shell
apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt update
apt-cache policy docker-ce
sudo apt install docker-ce
sudo systemctl status docker
```

* [install docker-compose](https://docs.docker.com/compose/install/)
```shell
sudo curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
ll -trh /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
docker-compose --version
```

* `docker login`

```shell

mkdir -p /usr/app/docker
cd /usr/app/docker

vi docker-compose.yml

vi breakcontent.env

mkdir nginx
vi nginx/default.conf
vi nginx/nginx.conf

# (optional, not required in prd env)
mkdir postgresql
vi postgresql/init.sql

# up 
docker-compose up -d 

```


# how to set up RO user
設定RO 帳戶的方法

1. sudo -i -u postgres
2. psql
3. postgres=# CREATE USER acro WITH ENCRYPTED PASSWORD 'articleropass';
4. postgres=# alter user acro set default_transaction_read_only=on;
5. postgres=# GRANT USAGE ON SCHEMA public to acro;
6. postgres=# \c break_article
7. break_article=# grant select on all tables in schema public to acro;
8. break_article=# \q


================ 分隔線 ================

* issue

    - locale
    root@cc-psql:/home/ubuntu# locale
    locale: Cannot set LC_CTYPE to default locale: No such file or directory
    locale: Cannot set LC_ALL to default locale: No such file or directory
    LANG=en_US.UTF-8
    LANGUAGE=
    LC_CTYPE=UTF-8
    LC_NUMERIC="en_US.UTF-8"
    LC_TIME="en_US.UTF-8"
    LC_COLLATE="en_US.UTF-8"
    LC_MONETARY="en_US.UTF-8"
    LC_MESSAGES="en_US.UTF-8"
    LC_PAPER="en_US.UTF-8"
    LC_NAME="en_US.UTF-8"
    LC_ADDRESS="en_US.UTF-8"
    LC_TELEPHONE="en_US.UTF-8"
    LC_MEASUREMENT="en_US.UTF-8"
    LC_IDENTIFICATION="en_US.UTF-8"
    LC_ALL=

    - [solution](https://askubuntu.com/questions/599808/cannot-set-lc-ctype-to-default-locale-no-such-file-or-directory)

# issue

    sudo apt-get install redis-server

    perl: warning: Setting locale failed.
    perl: warning: Please check that your locale settings:
        LANGUAGE = (unset),
        LC_ALL = (unset),
        LC_CTYPE = "UTF-8",
        LANG = "en_US.UTF-8"
        are supported and installed on your system.
    perl: warning: Falling back to a fallback locale ("en_US.UTF-8").
    locale: Cannot set LC_CTYPE to default locale: No such file or directory
    locale: Cannot set LC_ALL to default locale: No such file or directory

    - [solution](https://chingjs.wordpress.com/2017/03/02/linux-%E8%A7%A3%E6%B1%BA%E9%8C%AF%E8%AA%A4%E8%A8%8A%E6%81%AF-perl-warning-setting-locale-failed/)

    ```shell
    localectl list-locales
    sudo locale-gen zh_TW.UTF-8
    sudo update-locale LANG=zh_TW.UTF-8

    # Then restart the system or open a new terminal.


    ```

    - [ref](https://www.thomas-krenn.com/en/wiki/Configure_Locales_in_Ubuntu)


* issue: 

    - [solution](https://github.com/docker/compose/issues/6023)
    Follow @shin-'s advice:

    > Please follow the official install instructions instead: https://docs.docker.com/compose/install/

    don't do `apt install docker-compose` and if you did, remove it and its dependencies: `apt remove docker-compose -y && apt autoremove`.
    With the official installation the problem's gone.

    - [solution](https://docs.docker.com/compose/install/)
