import sqlite3
from elasticsearch import Elasticsearch

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
if es.ping():
    # Index settings
    settings = {
        "mappings": {
            "_doc": {
                "dynamic": "strict",
                "properties": {
                    "id": {
                        "type": "text"
                    },
                    "title": {
                        "type": "text"
                    },
                    "description": {
                        "type": "text"
                    },
                }
            }
        }
    }
    es.indices.create(index='movies_index', ignore=400, body=settings)
    conn = sqlite3.connect('/var/sqlite/db/movies.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies;")
    results = cursor.fetchall()
    for result in results:
        movie_obj = {
            'type': 'movies',
            'id': result[0],
            'title': result[1],
            'description': result[2],
        }
        # Store document in Elasticsearch
        res = es.index(index='movies_index', id=result[0], body=movie_obj)
        pass
else:
    print("Unexpected error")
