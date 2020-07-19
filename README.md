https://praktikum.yandex.ru

## Usage

* Run search using sqlite fts: http://127.0.0.1:5000/search?key=географ
* Run search using elastic: http://127.0.0.1:5000/search?key=географ&index=elastic

Running the ElasticSearch container separately could be useful during development.

```
docker-compose up --no-deps --build elasticsearch
```

Open http://localhost:9200/.

![elasticsearch_screenshot]

```
curl -X GET http://localhost:9200/movies_index/_search \
-H "Content-Type: application/json" \
-d '{
  "query": {
    "bool": {
      "must": {
        "match": {
          "title": "географ"
        }
      }
    }
  }
}'
```

Run the [Kibana](https://www.elastic.co/kibana) container separately to access indexed content.

```
docker-compose up --no-deps --build kibana
```

Open http://localhost:5601/app/kibana#/dev_tools/console and try to run example query:

```
GET movies_index/_search
{
  "query": {
    "bool": {
      "must": {
        "match": {
          "title": "географ"
        }
      }
    }
  }
}
```

```
GET movies_index/_search
{
  "query": {
    "multi_match" : {
      "query": "географ", 
      "fields": [ "title", "description" ] 
    }
  }
}
```

![kibana_screenshot]

* [Command Line Shell For SQLite](https://sqlite.org/cli.html)
* [SQLite FTS5 Extension](https://www.sqlite.org/fts5.html)
* [Full-text Query Syntax](https://www.sqlite.org/fts5.html#full_text_query_syntax)

[elasticsearch_screenshot]: common/elasticsearch.png
[kibana_screenshot]: common/kibana.png
