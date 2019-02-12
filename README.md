# Content Core

### Prerequisite

### Dev env
* ip: 192.168.18.111

### Stg env
* AC IP: 35.236.166.182
* AC/CC PSQL GCP IP: 35.194.207.202
* CC GCP IP: 35.234.56.85
* CC IDC IP: 112.121.109.120 (192.168.250.140) (ubuntu/1qaz@WSX)

### Prd env & spec
| Machine | FQDN/IP | CPU | RAM | DISK | Pub_IP |
|:-------:|:--------:|:---:|:---:|:----:|:-----:|
| CC Server | 192.168.18.? | 10vCPU | 38G | 100G | Y |
| CC Redis | 192.168.18.? | 2vCPU | 15G | 60G | N |
| CC PSQL | 192.168.18.? | 6vCPU | 30G |400G | N |

### todo list
1. selenium for infinity page
2. extract domain/bsp specific rules from code
2. og and item parser
3. study bs4
4. install psql with password
5. install redis with password

### Installation
#### IDC dev env
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
* Endpoint: ```GET /v1/partner/setting/{partner_id}/{domain}```

* Header:
    - Content-Type: application/json

| Parameter | Type | Default/Required | Description | Example |
|:---------:|:----:|:----------------:|:-----------:|:-------:|
| ```xpath``` | ```String``` | N |  |  |
| ```e_xpath``` | ```String``` | N |  |  |
| ```category``` | ```String``` | N |  |  |
| ```e_category``` | ```String``` | N |  |  |
| ```authorList``` | ```String``` | N |  |  |
| ```e_authorList``` | ```String``` | N |  |  |
| ```regex``` | ```String``` | N |  |  |
| ```e_title``` | ```String``` | N |  |  |
| ```syncDate``` | ```String``` | N |  |  |
| ```page``` | ```String``` | N |  |  |
| ```delayday``` | ```String``` | N |  |  |
| ```sitemap``` | ```String``` | N |  |  |


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

# AC PSQL access info
* How to enter postgresql:
* psql -p5432 -Upostgres -h 35.194.207.202 / password: admin
* db: break_article
