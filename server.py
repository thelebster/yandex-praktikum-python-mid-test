from flask import Flask, request, jsonify
import os
import json
import logging
import sqlite3

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app = Flask(__name__)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    try:
        logging.info("Service is up and running.")
        sqlite_version = sqlite3.sqlite_version
        return jsonify({
            "message": "Service is up and running.",
            "sqlite_version": sqlite_version,
        })
    except Exception as e:
        logging.error("Unexpected error: %s" % e)
        return jsonify({"error": "Service unavailable."}), 500


@app.route('/search', methods=['GET'])
def search():
    try:
        search_key = request.args.get('key', '')
        if not search_key.strip():
            return jsonify({"error": "Search key could not be empty."}), 400

        conn = sqlite3.connect('/var/sqlite/db/movies.db')
        cursor = conn.cursor()
        sql_query = "SELECT movies.id, movies.title, movies.description, movies.file_path " \
                    "FROM movies_index " \
                    "LEFT JOIN movies ON movies.id = movies_index.rowid " \
                    "WHERE movies_index MATCH ?"
        cursor.execute(sql_query, ('%s*' % search_key,))
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        logging.error("Unexpected error: %s" % e)
        return jsonify({"error": "Service unavailable."}), 500


FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = os.getenv('FLASK_PORT', 5000)
if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)
