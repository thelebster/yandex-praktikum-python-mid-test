https://praktikum.yandex.ru

## Intro

* SQLite хорошо справляется с локальным хранением данных и не масштабируется горизонтально. Нет ограничений на чтение, 
но в один момент времени возможна только одна операция записи.
* SQLite с версии [3.9.0](https://www.sqlite.org/releaselog/3_9_0.html) включает расширение для полнотекстового поиска [FTS5](https://www.sqlite.org/fts5.html),
которое вполне себе работает.
* Поскольку с масштабирование SQLite не задалось, то для решения задачи полнотекствого поиска можно использовать [Elasticsearch](https://www.elastic.co/elasticsearch/),
который отлично масштабируется (но любит память, так как написан на Java). 
* Одно из условий — учитывать морфологию при поиске. Например, приводить слово к нормальной форме "люди -> человек", 
или "гулял -> гулять" и другое.
    
    Для того чтобы лучше разобраться с тем как работает и что делает морфологический анализатор, 
можно посмотреть на модуль [pymorphy2](https://github.com/kmike/pymorphy2).

    Для нашей задачи это решение не очень подходит, так как слова в заголовке или описании могут быть в любой форме, числе или падеже, 
и придется строить сложный запрос для поиска учитывая все варианты написания слов.

    Более элегантный путь — использование плагина [Morphological Analysis](https://github.com/imotov/elasticsearch-analysis-morphology) для Elasticsearch, 
который строится на базе https://github.com/AKuznetsov/russianmorphology. К сожалению, плагин стабильно работает только для Elasticsearch 5.6.x.
* В БД дополнительно хранится ссылка на .srt файл, по нему тоже нужно искать. Для решения этой задачи самый простой и очевидный путь — 
хранить содержимое файла как поле в индексе Elasticsearch.

## References

* [Appropriate Uses For SQLite](https://www.sqlite.org/whentouse.html)
* [SQLite vs MySQL vs PostgreSQL: A Comparison Of Relational Database Management Systems](https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems)
* [Command Line Shell For SQLite](https://sqlite.org/cli.html)
* [SQLite FTS5 Extension](https://www.sqlite.org/fts5.html) — FTS5 is an SQLite virtual table module that provides full-text search functionality to database applications.
* [Full-text Query Syntax](https://www.sqlite.org/fts5.html#full_text_query_syntax)
* [Elasticsearch Reference](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
* [Multi-match query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html)
* [SQLite Tutorial](https://www.sqlitetutorial.net)
* [Morphological analyzer (POS tagger + inflection engine) for Russian language](https://github.com/kmike/pymorphy2)

## Usage

```
cp .env.sample .env

docker-compose up --build
```

* Run search using sqlite fts: `curl -X GET 'http://127.0.0.1:5000/search?key=географ'`
* Run search using elastic: `curl -X GET 'http://127.0.0.1:5000/search?key=географ&index=elastic'`
* List movies: `curl -X GET 'http://127.0.0.1:5000/movies'`
* Retrieve a single movie: `curl -X GET 'http://127.0.0.1:5000/movies/105740'`
* Delete a single movie: `curl -X DELETE 'http://127.0.0.1:5000/movies/105740'`
* Insert a single movie:
```
curl --location --request POST 'http://127.0.0.1:5000/movies/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "id": 100500,
    "title": "Super Movie",
    "description": "Yo! Some super movie description."
}'
```
* Update a single movie:
```
curl --location --request PUT 'http://127.0.0.1:5000/movies/100500' \
--header 'Content-Type: application/json' \
--data-raw '{
    "title": "Super Movie (updated)",
    "description": "Yo! Some super movie description (updated)."
}'
```

Running the Elasticsearch container separately could be useful during development.

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

[elasticsearch_screenshot]: common/elasticsearch.png
[kibana_screenshot]: common/kibana.png
