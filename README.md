# Content Core

### Dev env
* 192.168.18.111

### Stg env
| Machine | private IP | CPU | RAM | DISK | Pub_IP | Desc |
|:-------:|:--------:|:---:|:---:|:----:|:-----:|:----:|
| stg-cc | 10.140.0.56 | 4 | 7.5G | 40G | 35.229.131.198 | nginx,redis,web,workers |
| stg-cc-psql | 10.140.15.248 | 4 | 15G | 50G | N | postgres/ContentBreak_psql1qaz |
| stg-AC(stg-article-content-dev-worker) | 10.140.0.17 |||||
| stg-PS | stg-partner.breaktime.com.tw |||||


### Prd-GCP env & spec 
* Compute Engine

| Machine | private IP | CPU | RAM | DISK | Pub_IP | Desc |
|:-------:|:--------:|:---:|:---:|:----:|:-----:|:----:|
| prd-cc-psql | 10.140.0.127 | 16vCPU | 15G | 250G | N | postgres/ContentBreak_psql1qaz |
| prd-cc-redis | 10.140.0.119 | 2vCPU | 13G | 50G | N | pw: ContentBreak_1qaz |
| prd-cc-web | 10.140.15.210 | 2vCPU | 13G | 50G | Y | |
| prd-cc-worker | dynamic | 2vCPU | 4.5G | 20G | N | for deployment use only |

* prd-cc-worker-group spec

| CPU | RAM | DISK | MIN | MAX |
|:---:|:---:|:----:|:---:|:---:|
| 8 | 15G | 20G | 1 | 3 | 

### Prd-IDC env & spec
| Machine | FQDN/IP | CPU | RAM | DISK | Pub_IP |
|:-------:|:--------:|:---:|:---:|:----:|:-----:|
| CC Server | 192.168.18.121 | 10vCPU | 38G | 100G | 112.121.109.124 |
| CC Worker | 192.168.18.124 | 10vCPU | 38G | 100G | N |
| CC Worker2 | 192.168.18.125 | 10vCPU | 10G | 100G | N |
| CC Worker3 | 192.168.18.126 | 10vCPU | 10G | 100G | N |
| CC Redis | 192.168.18.122 | 2vCPU | 30G | 60G | N |
| CC PSQL | 192.168.18.123 | 6vCPU | 30G | 400G | N |

* copy pub_key to remote machine for passwordless login, example:
```
ssh-copy-id -i ~/.ssh/id_rsa ubuntu@192.168.18.121
ssh ubuntu@192.168.18.121
```

### Todo list (mine)
1. selenium for infinity page
2. extract domain/bsp specific rules from code
2. og and item parser
3. study bs4
4. [enhance aujs detect](https://docs.google.com/spreadsheets/d/15P93Nn2Yon5jMQpKWmstLkpwHM7p49-t5YCNdcZIGKk/edit#gid=18960491)

### Todo list (after 2019.3.14 discussion w/ joy)
1. ads.txt scanning (as jphf w/ DFP api)
2. if div exists in html?
3. if ads.txt in root domain or sub domain?
4. div id with prefix 'zi_ad_*'
5. https://zi.media/robots.txt
6. https://zi.media/ads.txt
7. https://docs.google.com/spreadsheets/d/1tA_322BEnBuC2uE9xghpruDJzmgZL5IDhIAWjb50I0I/edit#gid=594128750

### Todo list to Alan (day cost: > 20d)
1. CC statistic cronjob (3d)
2. CC migrate from GCP to IDC (3d)
3. enhanced aujs detection (1d)
4. itemprop/og parsing (5d)
5. extract domain/bsp specific rules from code (5d)
6. detecting div id with prefix 'zi_ad_*' (1d, discussion required)
7. ads.txt (discussion required)
8. robot.txt (discussion reuqired)
9. selenium for js decorated page (depends)
10. CC deployment on K8S (2d)


---
### CC Endpoints & purpose
1. Inform CC a crawler task
2. Trigger a task to run
3. Get content from CC

#### Inform CC a crawler task
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
curl -v -X POST 'http://localhost:80/v1/task' -H 'Content-Type: application/json' -d '{"url": "https://www.kocpc.com.tw/archives/693", "url_hash": "a6d62aaef4856b23d7d8016e4e77409001d999fa", "priority": 1, "partner_id": "3WYST18", "generator": "WordPress2", "notexpected": "blablabla"}'
```
```json
{
  "msg": "",
  "status": true
}
```

#### Trigger a task to run
**Request**
* Endpoint: ```GET /v1/create_tasks/{priority: int}```
**Example**
```shell
curl -v -X GET 'http://localhost:80/v1/create_tasks/1'
# do cmd every {5} sec
watch -n5 curl -v -X GET 'http://192.168.18.121:80/v1/create_tasks/1'
```
```json
{
  "msg": "ok",
  "status": true
}
```

#### Get content from CC
**Request**
* Endpoint: ```GET /v1/content/{url_hash}```

**Example**
```shell
curl -v -X GET -H 'Content-Type: application/json' 'http://localhost:80/v1/content/a6d62aaef4856b23d7d8016e4e77409001d999fa'
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

#### Update domain specific config in CC
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
curl -v -X PUT -H 'Content-Type: application/json' 'http://localhost:80/v1/partner/setting/3WYST18/www.kocpc.com.tw' -d '{"xpath": "blablabla"}'
```
```json
{
  "msg": "ok",
  "status": true
}
```
---
### AC Endpoints & purpose
#### Register url & send request to CC
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


#### Inform AC when the crawler is done
**Request**
* Endpoint: ```PUT /v1/content/status```

**Example**
```shell
curl -H "Content-Type: application/json; charset=UTF-8" -X PUT "http://35.236.166.182:80/v1/content/status" -d '{"url": "https://www.kocpc.com.tw/archives/693", "url_hash": "13e83fc609e45fc3aea1bedac006629bee505265", "content_update": false, "request_id": "ef114158-b445-4285-bebf-b129d8b7e0df", "publish_date": "2018-12-29 06:22:00.000Z", "parent_url": "http://d0169953.crlab.com.tw/?p=23", "url_structure_type": "content", "secret": false, "has_page_code": true, "status": "True", "quality": true, "old_url_hash": "847844911ffe6af2d9d9fcee69ab10f7cb2db63f"}'
```
```json
{"data":{}, "message": "OK"}
```
---

### Partner System Endpoints & purpose
#### Get domain info from PS
**Request**
* Endpoint: `GET /api/config/<domain>/<partner_id>`

**Example**
```shell
curl -v -X GET 'https://partner.breaktime.com.tw/api/config/YUZ7T18/healthnice.org/'
```
```json
{"status": true, "data": {"regex": [{"type": "NOT_MATCH_REGEX", "value": "fbclid"}, {"type": "NOT_MATCH_REGEX", "value": "category"}, {"type": "NOT_MATCH_REGEX", "value": "tag"}, {"type": "NOT_MATCH_REGEX", "value": "author"}, {"type": "NOT_MATCH_REGEX", "value": "\\?s"}, {"type": "NOT_MATCH_REGEX", "value": "page"}, {"type": "NOT_MATCH_REGEX", "value": "search"}, {"type": "MATCH_REGEX", "value": ".*"}], "xpath": ["//section[@class='post-contents']"]}, "message": "OK", "token": "7fde5828-6ee1-43ce-9d84-b76eda51ec8f"}
```

---

## Deployment

* always turn off beat before deployment
* reset redis if necessary
* you can deploy only the code-affected component

### HOWTO add a column w/o restarting db
* do it with sql client gui (handy)
```sql
ALTER TABLE task_service ADD status_code SMALLINT;
```

### HOWTO backup psql db in another machine
* backup psql from other machine
* must have psql cmd installed
```shell
sudo su
mkdir -p /etc/break_backup/
cd
vi psql_backup.sh

#!/bin/bash
today=`date +%Y-%m-%d-%H:%M`
backupdir="/etc/break_backup/"
PGPASSWORD=ContentBreak_psql1qaz pg_dump -d break_content -U postgres -h 10.140.0.127 -f "$backupdir"break_content_"$today".sql
find $backupdir -name "break_content*" -mtime +2 -type f -exec rm -rf {} \;

chmod +x psql_backup.sh

crontab -e 
5 */3 * * * /root/psql_backup.sh
```
* import *.sql into psql
```shell
# example
PGPASSWORD=admin psql -h localhost -U postgres -e break_content < break_content_2019-02-27-03\:44.sql
```

### Restart container every 3 hour
* to prevent unexpected hanging
```
crontab -e 
5 */3 * * * docker-compose -f /usr/app/docker/docker-compose.yml restart worker-xpcrawler
```

### HOWTO deploy on to GCP K8S
* link github repo under gcp project

---

### HOWTO optimize PSQL
* spec: SSD disk with RAM 15G
```sh
vi /etc/postgresql/10/main/postgresql.conf

shared_buffers=10GB #10 ~ 25% suggested
work_mem=500MB # 2~4%
max_connections=200
effective_cache_size=13
maintence_work_mem=512M
log_min_duration_statement = 250

service postgresql restart
systemctl status postgresql

# note
max_connections * work_mem < total RAM
```


### HOWTO initiate psql db
* First make sure the container is not running
```shell
docker-compose down -v
```
* @ prd psql machine(192.168.18.123)
```shell
ssh ubuntu@192.168.18.123
psql -U postgres -h localhost
PGPASSWORD=ContentBreak_psql1qaz psql -U postgres -h localhost -d break_content
#pw: ContentBreak_psql1qaz
#pw: ArticleBreak_psql1qaz
```
* recreate db (enter psql shell)
```sql
SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'break_content'
      AND pid <> pg_backend_pid();
DROP DATABASE break_content;
CREATE DATABASE break_content;
# \q
```
* recreate db (w/o entering psql shell)
```sql
psql -h localhost -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'break_content' AND pid <> pg_backend_pid()"
psql -h localhost -U postgres -c 'DROP DATABASE break_content'
psql -h localhost -U postgres -c 'CREATE DATABASE break_content'
```
* run sql syntax from psql cmdline (w/ password attached)
```sql
PGPASSWORD=ContentBreak_psql1qaz psql -h localhost -U postgres -d break_content -c 'SELECT count(id) FROM task_main'
```

* db operation
```sql
\c break_content
#\d+ <table name>
\d+ task_service
```

### HOWTO move docker image btw machine
* from dev to prd (local > remote)
```shell
# @ dev 192.168.18.111
docker save -o /home/lance/playground/cc.tar cc
scp /home/lance/playground/cc.tar root@192.168.18.121:/usr/app/docker/
# @ prd 192.168.18.121
docker load -i /usr/app/docker/cc.tar
```

### HOWTO generate sshkey & pass it to remote machine
```sh
ssh-keygen
ssh-copy-id user@remote_ip
```

### HOWTO monitor psql
* Run this SQL to see postgresql max connections allowed:
```sql
show max_connections;
```
* Take a look at exactly who/what/when/where is holding open your connections:
```sql
SELECT * FROM pg_stat_activity;
```
* The number of connections currently used is
```sql
SELECT COUNT(*) from pg_stat_activity;
```
* check client conn count
```sql
SELECT client_addr,count(*) from pg_stat_activity group by client_addr order by count desc;
```
* check task status 
```sql
select status,count(id) from task_main group by status order by count desc;
```
* check tasks status by priority
```sql
select priority,status,count(id) from task_main group by priority,status;
```
* check single/multi-page status
```sql
select b.is_multipage,a.status,count(a.id) from task_main as a, task_service as b where b.task_main_id = a.id group by b.is_multipage,a.status;
```
* group by if partner or not
```sql
select case when partner_id is null then false else true end as pbool,priority,status,count(id) from task_main group by pbool,priority,status order by pbool desc,priority,status;
```
* group by time interval
```sql
SELECT COUNT(*) cnt, to_timestamp(floor((extract('epoch' from _ctime) / 600 )) * 600) AT TIME ZONE 'UTC' as interval_alias FROM task_main GROUP BY interval_alias order by interval_alias;
```
### HOWTO monitor celery



### HOWTO install [Stackdriver](https://cloud.google.com/monitoring/agent/install-agent#linux-install) agent
* for system monitoring
```shell
cd
curl -sSO https://dl.google.com/cloudagents/install-monitoring-agent.sh
sudo bash install-monitoring-agent.sh
sudo service stackdriver-agent status
# if necessary
sudo service stackdriver-agent restart
```

### HOWTO reset Redis
* 清空production redis broker:
```shell
redis-cli -a ContentBreak_1qaz -n 4
# select <db_index>
DBSIZE
flushall
```

### HOWTO logging
* [google-cloud-logging](https://googleapis.github.io/google-cloud-python/latest/logging/stdlib-usage.html)
* err msg
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials. Please set GOOGLE_APPLICATION_CREDENTIALS or explicitly create credentials and re-run the application. For more information, please see https://cloud.google.com/docs/authentication/getting-started
```
* [Python Logging Module Handler](https://google-cloud.readthedocs.io/en/latest/logging/handlers.html)
* [Integration with Python logging module](https://googleapis.github.io/google-cloud-python/latest/logging/stdlib-usage.html)
* [logging to kafka](https://github.com/openstack/monasca-analytics/blob/master/monasca_analytics/util/common_util.py)
* [install logging agent](https://cloud.google.com/logging/docs/agent/installation#joint-install)
* [issue w/ solution](https://github.com/googleapis/google-cloud-python/issues/7719)


* test credential
```shell
pipenv shell

export GOOGLE_APPLICATION_CREDENTIALS="/home/lance/breaktime.ContentCore/data-alchemy-181502-3e950935b524.json"

# enter python interactive mode
python 
```
```python
# def implicit():
from google.cloud import storage
# If you don't specify credentials when constructing the client, the
# client library will look for credentials in the environment.
storage_client = storage.Client()
# Make an authenticated API request
buckets = list(storage_client.list_buckets())
print(buckets)
# implicit()
```
* output
```
[<Bucket: artifacts.data-alchemy-181502.appspot.com>, <Bucket: prd_catalyst_bucket>, <Bucket: prd_catalyst_file>, <Bucket: prd_catalyst_log_bucket>]
```

### HOWTO implement JWT token
```python
def create_zi_token():
    payload = {
        "iss": "breaktime.com.tw",
        "aud": "zi.media",
        "username": "article_center",
    }
    token = jwt.encode(payload, 'secret', algorithm='HS256')
    return token
def verify_zi_token(token):
    #  如果在生成token的时候使用了aud参数，那么校验的时候也需要添加此参数
    payload = jwt.decode(token, 'secret', audience='zi.media', algorithms=['HS256'])
    if payload:
        return True, payload
    return False, token
    
# PS: JWT 實作範例：https://segmentfault.com/a/1190000010312468
# PS: JWT 預設payload 說明：https://www.jianshu.com/p/3d4a1a124ef5
```
