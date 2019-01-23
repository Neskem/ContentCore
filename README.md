# Content Core

### Prerequisite

### Installation
* clone the repo
* cd docker/
* docker-compose up -d

# Usage

# CC Endpoints & purpose

### inform CC a crawler task
**Request**

* Endpoint: ```POST /v1/task```
* Content-Type: ```application/json```

| Parameter | Type | Default/Required | Description | Example |
|:---------:|:----:|:----------------:|:-----------:|:-------:|
| ```request_id``` | ```String``` | Y | request id | aaaa619f-576c-4473-add2-e53d08b74ac7 |
| ```url``` | ```String``` | Y | url| https://www.kocpc.com.tw/archives/693 |
| ```url_hash``` | ```String``` | Y | url hash encoded by AC | a6d62aaef4856b23d7d8016e4e77409001d999fa |
| ```partner_id``` | ```String``` | N | partner id | 3WYST18 |
| ```generator``` | ```String``` | N | generator | WordPress2, PChoc, blogger, |

**Example**
```shell
curl -v -X POST 'http://localhost:8100/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "aaaa619f-576c-4473-add2-e53d08b74ac7", "url": "https://www.kocpc.com.tw/archives/693", "url_hash": "a6d62aaef4856b23d7d8016e4e77409001d999fa", "priority": 1, "partner_id": "3WYST18", "generator": "WordPress2", "notexpected": "blablabla"}'
```
```json
{
  "msg": "",
  "status": true
}
```

### trigger a task to run
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

### get content from CC
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


### AC Endpoints & purpose
* register url & send request to CC
```shell
curl -X GET 'http://35.236.166.182:80/v1/admin/service/sync?service\_name=Zi_C&status=sync&partner_id=3WYST18&url=https://www.kocpc.com.tw/archives/693'
```

* inform AC when crawler is done
```shell
curl -H "Content-Type: application/json; charset=UTF-8" -X PUT "http://35.236.166.182:80/v1/content/status" -d '{"url": "https://www.kocpc.com.tw/archives/693", "url_hash": "13e83fc609e45fc3aea1bedac006629bee505265", "content_update": false, "request_id": "ef114158-b445-4285-bebf-b129d8b7e0df", "publish_date": "2018-12-29 06:22:00.000Z", "parent_url": "http://d0169953.crlab.com.tw/?p=23", "url_structure_type": "content", "secret": false, "has_page_code": true, "status": "True", "quality": true, "old_url_hash": "847844911ffe6af2d9d9fcee69ab10f7cb2db63f"}'
```

{“data”:{},“message”:“OK”}

# AC PSQL access info
How to enter postgresql:
psql -p5432 -Upostgres -h 35.194.207.202 / password: admin
db: break_article
