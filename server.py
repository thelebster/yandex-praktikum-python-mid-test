from flask import Flask, request, jsonify
import os
import logging
import sqlite3
from elasticsearch import Elasticsearch

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app = Flask(__name__)

SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', '/var/sqlite/db/movies.db')


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    try:
        logging.info("Service is up and running.")
        sqlite_version = sqlite3.sqlite_version
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        es_status = None
        try:
            es_status = es.info()
        except Exception as e:
            logging.error("Unexpected error: %s" % e)
        return jsonify({
            "message": "Service is up and running.",
            "sqlite_version": sqlite_version,
            "elasticsearch_status": es_status,
        })
    except Exception as e:
        logging.error("Unexpected error: %s" % e)
        return jsonify({"error": "Service unavailable."}), 500


def sqlite_search(search_key):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    sql_query = "SELECT movies.id, movies.title, movies.description, movies.file_path " \
                "FROM movies_index " \
                "LEFT JOIN movies ON movies.id = movies_index.rowid " \
                "WHERE movies_index MATCH ?"
    cursor.execute(sql_query, ('%s' % search_key,))
    results = cursor.fetchall()
    return results


def elastic_search(search_key):
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    search_object = {
        'query': {
            'multi_match': {
                "query": search_key,
                "fields": [
                    "title",
                    "description",
                ],
            }
        }
    }
    results = es.search(index='movies_index', body=search_object)
    return results['hits']['hits']


@app.route('/search', methods=['GET'])
def search():
    try:
        search_key = request.args.get('key', '')
        if not search_key.strip():
            return jsonify({"error": "Search key could not be empty."}), 400

        search_index = request.args.get('index', 'sqlite')
        if search_index == 'elastic':
            results = elastic_search(search_key)
        else:
            results = sqlite_search(search_key)
        return jsonify(results)
    except Exception as e:
        logging.error("Unexpected error: %s" % e)
        return jsonify({"error": "Service unavailable."}), 500


@app.route('/movies', methods=['GET', 'POST'])
@app.route('/movies/<int:movie_id>', methods=['GET', 'PUT', 'DELETE'])
def movies(movie_id=None):
    try:
        if request.method == 'GET':
            if movie_id is not None:
                conn = sqlite3.connect(SQLITE_DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id, title, description FROM movies "
                               "WHERE id = ?", ('%d' % movie_id,))
                results = cursor.fetchone()
                return jsonify(results)

            offset = int(request.args.get('offset', 0))
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, description FROM movies "
                           "LIMIT 20 OFFSET ?", ('%d' % offset,))
            results = cursor.fetchall()
            return jsonify(results)

        if request.method == 'POST':
            movie_id = str(request.json.get('id', ''))
            if not movie_id.strip():
                return jsonify({"error": "Movie id could not be empty."}), 400

            movie_title = request.json.get('title', '')
            if not movie_title.strip():
                return jsonify({"error": "Movie title could not be empty."}), 400

            movie_description = request.json.get('description', '')
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO movies (id, title, description) "
                           "VALUES (?, ?, ?)", ('%s' % movie_id, '%s' % movie_title, '%s' % movie_description))
                conn.commit()
                # Store a document in the Elasticsearch index
                movie_obj = {
                    'type': 'movies',
                    'id': movie_id,
                    'title': movie_title,
                    'description': movie_description,
                }
                es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
                index_result = es.index(index='movies_index', id=movie_id, body=movie_obj)
            except sqlite3.Error as e:
                conn.rollback()
                raise e
            except Exception as e:
                raise e
            finally:
                cursor.close()
            return jsonify({
                'rowid': cursor.lastrowid,
                'index': index_result,
            })

        if request.method == 'PUT':
            movie_title = request.json.get('title', '')
            if not movie_title.strip():
                return jsonify({"error": "Movie title could not be empty."}), 400

            movie_description = request.json.get('description', '')
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE movies SET title = ?, description = ?"
                               "WHERE id = ?", ('%s' % movie_title, '%s' % movie_description, '%s' % movie_id))
                conn.commit()
                # Update a document in the Elasticsearch index
                movie_obj = {
                    'type': 'movies',
                    'id': movie_id,
                    'title': movie_title,
                    'description': movie_description,
                }
                es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
                index_result = es.index(index='movies_index', id=movie_id, body=movie_obj)
            except sqlite3.Error as e:
                conn.rollback()
                raise e
            except Exception as e:
                raise e
            finally:
                cursor.close()
            return jsonify({
                'rowid': cursor.lastrowid,
                'index': index_result,
            })

        if request.method == 'DELETE':
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM movies "
                               "WHERE id = ?", ('%s' % movie_id,))
                conn.commit()
                # Delete a document from the Elasticsearch index
                es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
                index_result = es.delete(index='movies_index', id=movie_id)
            except sqlite3.Error as e:
                conn.rollback()
                raise e
            except Exception as e:
                raise e
            finally:
                cursor.close()
            return jsonify({
                'index': index_result,
            })
    except Exception as e:
        logging.error("Unexpected error: %s" % e)
        return jsonify({"error": "%s" % e}), 500


FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = os.getenv('FLASK_PORT', 5000)
if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)
