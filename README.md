# Content Core

### Prerequisite
test from win

### Dev env
* ip: 192.168.18.111

### Stg env
* AC IP: 35.236.166.182
* AC/CC PSQL GCP IP: 35.194.207.202
* CC GCP IP: 104.155.194.18 (10.140.0.17)
* CC IDC IP: 112.121.109.120 (192.168.250.140) (ubuntu/1qaz@WSX)

### Prd env & spec
| Machine | FQDN/IP | CPU | RAM | DISK | Pub_IP |
|:-------:|:--------:|:---:|:---:|:----:|:-----:|
| CC Server | 192.168.18.121 | 10vCPU | 38G | 100G | 112.121.109.124 |
| CC Redis | 192.168.18.122 | 2vCPU | 15G | 60G | N |
| CC PSQL | 192.168.18.123 | 6vCPU | 30G | 400G | N |

ubuntu/1qaz@WSX

* copy pub_key to remote machine for passwordless login, example:
```
ssh-copy-id -i ~/.ssh/id_rsa ubuntu@192.168.18.121

ssh ubuntu@192.168.18.121
```

### todo list
1. selenium for infinity page
2. extract domain/bsp specific rules from code
2. og and item parser
3. study bs4
4. install psql with password
5. install redis with password
6. [enhance aujs detect](https://docs.google.com/spreadsheets/d/15P93Nn2Yon5jMQpKWmstLkpwHM7p49-t5YCNdcZIGKk/edit#gid=18960491)

### Depolyment
* on prd (only docker image are required)
```shell



```

* on dev (source code are required to speed up development)
```shell
git clone blabla
cd docker/
check your settings (docker-compose.yml & breakcontent.env)
docker-compose up -d
```

#### GCP stg env
```shell
ssh changteanhsu@35.234.56.85
sudo su
apt-get install tmux
cd /home/lance
git clone blablabla
git pull origin develop
git checkout develop
git pull origin develop
apt-get install docker-compose
# check ip 
vi refresh.sh
```


## CC Endpoints & purpose
1. Inform CC a crawler task
2. Trigger a task to run
3. Get content from CC

### Inform CC a crawler task
**Request**

* Endpoint: ```POST /v1/task```
* Header:
    - Content-Type: application/json
    - X-REQUEST-ID: d5c7fd14-4987-4921-9ddc-e4d63cf6620a

| Parameter | Type | Default/Required | Description | Example |
|:---------:|:----:|:----------------:|:-----------:|:-------:|
| ```request_id``` | ```String``` | N | request id | aaaa619f-576c-4473-add2-e53d08b74ac7 |
| ```url``` | ```String``` | Y | url| https://www.kocpc.com.tw/archives/693 |
| ```url_hash``` | ```String``` | Y | url hash encoded by AC | a6d62aaef4856b23d7d8016e4e77409001d999fa |
| ```partner_id``` | ```String``` | N | partner id | 3WYST18 |
| ```generator``` | ```String``` | N | generator | WordPress2, PChoc, blogger, |



**Example**
```shell
curl -v -X POST 'http://localhost:8100/v1/task' -H 'Content-Type: application/json' -d '{"url": "https://www.kocpc.com.tw/archives/693", "url_hash": "a6d62aaef4856b23d7d8016e4e77409001d999fa", "priority": 1, "partner_id": "3WYST18", "generator": "WordPress2", "notexpected": "blablabla"}'
```
```json
{
  "msg": "",
  "status": true
}
```

### Trigger a task to run
**Request**

* Endpoint: ```GET /v1/create_tasks/{priority: int}```

**Example**
```shell
curl -v -X GET 'http://localhost:8100/v1/create_tasks/1'
# do cmd every {5} sec
watch -n5 curl -v -X GET 'http://192.168.18.121:80/v1/create_tasks/1'
```
```json
{
  "msg": "ok",
  "status": true
}
```



### Get content from CC
**Request**
* Endpoint: ```GET /v1/content/{url_hash}```

**Example**
```shell
curl -v -X GET -H 'Content-Type: application/json' 'http://localhost:8100/v1/content/a6d62aaef4856b23d7d8016e4e77409001d999fa'
```
```json
{
  "data": {
    "content": "blablabla",
    "cover": "https://images.zi.org.tw/kocpc/images/pic.pimg.tw/kocpc/4bcda6eb52024.jpg",
    "publishedAt": "2010-04-20T16:03:30",
    "title": "ANDROID\u624b\u6a5f\u7684\u53e6\u4e00\u500b\u5c0e\u822a\u9078\u64c7-NAVIKING \u5c0e\u822a\u738b",
    "url": "https://www.kocpc.com.tw/archives/693",
    "url_structure_type": null
  },
  "msg": "ok",
  "status": true
}
```

### Update domain specific config in CC
**Request**
* Endpoint: ```PUT/POST /v1/partner/setting/{partner_id}/{domain}```

* Header:
    - Content-Type: application/json

| Parameter | Type | Default/Required | Description | Example |
|:---------:|:----:|:----------------:|:-----------:|:-------:|
| `xpath` | `array` | Y |  |  |
| `e_xpath` | `array` | N |  |  |
| `category` | `array` | N |  |  |
| `e_category` | `array` | N |  |  |
| `authorList` | `array` | N |  |  |
| `e_authorList` | `array` | N |  |  |
| `regex` | `array` | Y |  |  |
| `e_title` | `array` | N |  |  |
| `syncDate` | `array` | N |  |  |
| `page` | `array` | N |  |  |
| `delayday` | `array` | N |  |  |
| `sitemap` | `array` | N |  |  |


**Example**
```shell
curl -v -X PUT -H 'Content-Type: application/json' 'http://localhost:8100/v1/partner/setting/3WYST18/www.kocpc.com.tw' -d '{"xpath": "blablabla"}'

```
```json
{
  "msg": "ok",
  "status": true
}
```

## AC Endpoints & purpose
### Register url & send request to CC
**Request**
* Endpoint: ```GET /v1/admin/service/sync?service\_name={service}&status={behavior}&partner_id={partner_id}&url={url}```

| Parameter | Type | Default/Required | Description | Example |
|:---------:|:----:|:----------------:|:-----------:|:-------:|
| ```service_name``` | ```String``` | Y | Zi_C | aaaa619f-576c-4473-add2-e53d08b74ac7 |
| ```status``` | ```String``` | Y | url| behavior, e.g. sync |
| ```partner_id``` | ```String``` | N | partner id | 3WYST18 |
| ```url``` | ```String``` | N | url | https://www.kocpc.com.tw/archives/693 |

**Example**
```shell
curl -X GET 'http://35.236.166.182:80/v1/admin/service/sync?service\_name=Zi_C&status=sync&partner_id=3WYST18&url=https://www.kocpc.com.tw/archives/693'
```


### Inform AC when the crawler is done
**Request**
* Endpoint: ```PUT /v1/content/status```

**Example**
```shell
curl -H "Content-Type: application/json; charset=UTF-8" -X PUT "http://35.236.166.182:80/v1/content/status" -d '{"url": "https://www.kocpc.com.tw/archives/693", "url_hash": "13e83fc609e45fc3aea1bedac006629bee505265", "content_update": false, "request_id": "ef114158-b445-4285-bebf-b129d8b7e0df", "publish_date": "2018-12-29 06:22:00.000Z", "parent_url": "http://d0169953.crlab.com.tw/?p=23", "url_structure_type": "content", "secret": false, "has_page_code": true, "status": "True", "quality": true, "old_url_hash": "847844911ffe6af2d9d9fcee69ab10f7cb2db63f"}'
```
```json
{"data":{}, "message": "OK"}
```


## Partner System Endpoints & purpose
### Get domain info from PS
**Request**
* Endpoint: `GET /api/config/<domain>/<partner_id>`

**Example**
```shell
curl -v -X GET 'https://partner.breaktime.com.tw/api/config/YUZ7T18/healthnice.org/'
```
```json
{"status": true, "data": {"regex": [{"type": "NOT_MATCH_REGEX", "value": "fbclid"}, {"type": "NOT_MATCH_REGEX", "value": "category"}, {"type": "NOT_MATCH_REGEX", "value": "tag"}, {"type": "NOT_MATCH_REGEX", "value": "author"}, {"type": "NOT_MATCH_REGEX", "value": "\\?s"}, {"type": "NOT_MATCH_REGEX", "value": "page"}, {"type": "NOT_MATCH_REGEX", "value": "search"}, {"type": "MATCH_REGEX", "value": ".*"}], "xpath": ["//section[@class='post-contents']"]}, "message": "OK", "token": "7fde5828-6ee1-43ce-9d84-b76eda51ec8f"}
```

# AC PSQL access info
* How to enter postgresql:
* psql -p5432 -Upostgres -h 35.194.207.202 / password: admin
* db: break_article

--
# prd operation

# howto add a column w/o restarting db
* do it with sql client gui (handy)
```sql
ALTER TABLE task_service ADD status_code SMALLINT;
```

# backup sql db to another machine
* @ prd psql machine(192.168.18.123)
```sh
#!/bin/bash
today=`date +%Y-%m-%d-%H:%M`
backupdir="/etc/break_backup/"
PGPASSWORD=ArticleBreak_psql1qaz pg_dump -d break_article -U postgres -h 10.140.0.122 -f "$backupdir"break_article_"$today".sql
find $backupdir -name "break_article*" -mtime +2 -type f -exec rm -rf {} \;
```

# recreate db in psql
* First make sure the container is not running
```shell
docker-compose down -v
```
* @ prd psql machine(192.168.18.123)
```shell
ssh ubuntu@192.168.18.123
psql -U postgres -h localhost
#pw: ContentBreak_psql1qaz

```
```sql
SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'break_content'
      AND pid <> pg_backend_pid();

DROP DATABASE break_content;
CREATE DATABASE break_content;

# \q

```
* db operation
```sql
\c break_content
#\d+ <table name>
\d+ task_service
```


# move docker image btw machine
* from local to prd
```shell
# @ dev 192.168.18.111
docker save -o /home/lance/playground/cc.tar cc

# @ prd 192.168.18.121
scp root@192.168.18.111:/home/lance/playground/cc.tar /usr/app/docker/

docker load -i /usr/app/docker/cc.tar
```
* from local to remote (add local's pub key into remote machine)
```shell
# @ dev 192.168.18.111
docker save -o /home/lance/playground/cc.tar cc

scp /home/lance/playground/cc.tar root@104.155.194.18:/usr/app/docker/

# @ stg 35.234.56.85 
docker load -i /usr/app/docker/cc.tar

```
