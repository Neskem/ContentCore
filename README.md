# Content Core

### Prerequisite

### Installation
* clone the repo
* cd docker/
* docker-compose up -d

### Usage




### AC test cmds from Alan
--
* register url & send request to CC
curl -X GET "http://35.236.166.182:80/v1/admin/service/sync?service\_name=Zi_C&partner_id=YUZ7T18&url=http://d0169953.crlab.com.tw/?p=2318"

* inform AC after crawler
curl -H "Content-Type: application/json; charset=UTF-8" -X PUT "http://35.236.166.182:80/v1/content/status" -d '{"url": "http://d0169953.crlab.com.tw/?p=2318", "url_hash": "13e83fc609e45fc3aea1bedac006629bee505265", "content_update": false, "request_id": "ef114158-b445-4285-bebf-b129d8b7e0df", "publish_date": "2018-12-29 06:22:00.000Z", "parent_url": "http://d0169953.crlab.com.tw/?p=23", "url_structure_type": "content", "secret": false, "has_page_code": true, "status": "True", "quality": true, "old_url_hash": "847844911ffe6af2d9d9fcee69ab10f7cb2db63f"}'

{“data”:{},“message”:“OK”}

# Alan PSQL DB access
How to enter postgresql:
psql -p5432 -Upostgres -h 35.194.207.202 / password: admin
db: break_article
