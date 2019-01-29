
#ZI-MEDIA API 

###  Sync Article

**Request**

* Endpoint: ```PUT https://excg.zi.media/js/v1/articles```
* Content-Type: ```application/json```
*  - Authorization Token  is requirement(Authorization: ```<token>```)

| Parameter | Type | Default/Required | Description |
|:---------:|:----:|:----------------:|-------------|
| ```payload``` | ```JSON``` | Require | data body|
```json
{
    "payload": {
        'url': <original url> (*require),
        'title': <title>(*require),
        'publishedAt': <article publishd datetime (isoformat)>,
        'content': <cotent>(*required)
    }
}
```

**Response**

| Parameter | Type | Description |
|:---------:|:----:|-------------|
| ```successful``` | ```Boolean``` | 
| ```statuscode``` | ```int``` | 

**Example**
```
 curl -v  -H "Content-Type: application/json" -H "Authorization: 944cb002-8014-425d-8664-619ef649d239" -X PUT -d "{'payload': {'url': 'https://www.jsimplelife.com/268932928922290/-x', 'title': '台北｜中正慢旅 × 台北植物園，我和城市的植物系，踏踏步在高密度的綠地小森林 - JAMIE慢森活', 'content': '<div></div>', 'publishedAt': "2008-09-15T15:53:00+05:00"}  https://excg.zi.media/js/v1/articles
HTTP/1.1 200 OK
Date: Mon, 08 Aug 2016 08:46:41 GMT
Content-Type: Content-Type: application/json
Content-Length: 177
Connection: keep-alive
```
```json
{
    "successful": true,
    "statuscode": 200
}
```

###  Delete Article

**Request**

* Endpoint: ```delete https://excg.zi.media/js/v1/articles```
* Content-Type: ```application/json```
*  - Authorization Token  is requirement(Authorization: ```<token>```)

| Parameter | Type | Default/Required | Description |
|:---------:|:----:|:----------------:|-------------|
| ```payload``` | ```JSON``` | Require | data body|
```json
{
    "payload": {
        'url': <original url> (*require),
        'offline': true(*option)
    }
}
```

**Response**

| Parameter | Type | Description |
|:---------:|:----:|-------------|
| ```successful``` | ```Boolean``` | 
| ```statuscode``` | ```int``` | 

**Example**
```
 curl -v  -H "Content-Type: application/json" -H "Authorization: 944cb002-8014-425d-8664-619ef649d239" -X DELETE -d "{'payload': {'url': 'https://www.jsimplelife.com/268932928922290/-x'} https://excg.zi.media/js/v1/articles
HTTP/1.1 200 OK
Date: Mon, 08 Aug 2016 08:46:41 GMT
Content-Type: Content-Type: application/json
Content-Length: 177
Connection: keep-alive
```
```json
{
    "successful": true,
    "statuscode": 200
}
```

###  Modify Article Original Url

**Request**

* Endpoint: ```POST https://excg.zi.media/stage/modify/ziurl```
* Content-Type: ```application/json```
*  - Authorization Token  is requirement(Authorization: ```<token>```)

| Parameter | Type | Default/Required | Description |
|:---------:|:----:|:----------------:|-------------|
| ```payload``` | ```JSON``` | Require | data body|
```json
{
    "payload": {
        'zi_url': <article original url> (*require),
        'change_url': <new article url> (*require)
    }
}
```

**Response**

| Parameter | Type | Description |
|:---------:|:----:|-------------|
| ```successful``` | ```Boolean``` | 
| ```statuscode``` | ```int``` | 

**Example**
```
curl -v  -H "Content-Type: application/json" -H "Authorization: 944cb002-8014-425d-8664-619ef649d239" -X DELETE -d "{'payload': {'zi_url': 'https://www.jsimplelife.com/268932928922290/-x', "change_url": "https://www.jsimplelife.com/268932928922290/"} https://excg.zi.media/js/v1/articles
HTTP/1.1 200 OK
Date: Mon, 08 Aug 2016 08:46:41 GMT
Content-Type: Content-Type: application/json
Content-Length: 177
Connection: keep-alive
```
```json
{
    "successful": true,
    "statuscode": 200
}
```

