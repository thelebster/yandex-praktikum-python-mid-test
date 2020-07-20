#!/bin/sh
set -e

if [ -n "${SQLITE_DB_PATH}" ]; then
  SQLITE_DB_PATH=$SQLITE_DB_PATH
else
  SQLITE_DB_PATH=/var/sqlite/db/movies.db
fi

mkdir -p /var/sqlite/db
if [ ! -f $SQLITE_DB_PATH ]; then
  sqlite3 $SQLITE_DB_PATH <<EOF
  CREATE TABLE movies (
    id text primary key,
    title text,
    description text,
    file_path text,
    srt_path text
  );

  -- Create a virtual table for movies to index content
  -- Uses an extension fts5 for full text searching https://www.sqlite.org/fts5.html
  -- Uses the "porter" tokenizer, check this link for definition: https://www.sqlite.org/fts3.html#tokenizer
  CREATE VIRTUAL TABLE movies_index USING fts5(title, description, tokenize=porter);

  -- We need to keep the two table movies and movies_index in sync,
  -- as we add or update or delete, trigger can do the trick
  -- rowid is a special column on the virtual table that store the unique value of the row, we use the same primary key of movies
  -- Trigger on CREATE
  CREATE TRIGGER after_movie_insert AFTER INSERT ON movies BEGIN
    INSERT INTO movies_index (
      rowid,
      title,
      description
    )
    VALUES(
      new.id,
      new.title,
      new.description
    );
  END;

  -- Trigger on movie title UPDATE
  CREATE TRIGGER after_movie_title_update UPDATE OF title ON movies BEGIN
    UPDATE movies_index SET title = new.title WHERE rowid = old.id;
  END;

  -- Trigger on movie description UPDATE
  CREATE TRIGGER after_movie_description_update UPDATE OF description ON movies BEGIN
    UPDATE movies_index SET description = new.description WHERE rowid = old.id;
  END;

  -- Trigger on DELETE
  CREATE TRIGGER after_movie_delete AFTER DELETE ON movies BEGIN
    DELETE FROM movies_index WHERE rowid = old.id;
  END;
EOF

  # Prepare dataset, select only required fields.
  cat /tmp/movies.json | \
    jq -r '.result[] | .["file_path"] = .share_link | [.id,.title,.description // "",.file_path // ""] | @csv' \
    > /tmp/movies.csv

  # Import movies from the csv file.
  sqlite3 $SQLITE_DB_PATH -separator "," -cmd ".mode csv" ".import /tmp/movies.csv movies" ".quit"
fi

if [ -n "${ES_HOST}" ]; then
  ES_HOST=$ES_HOST
else
  ES_HOST=ypp-es
fi

# Wait for Elasticsearch
MAX_RETRIES=20
retry=1
while ! nc -z $ES_HOST 9200;
do
  if [ ""$retry -gt $MAX_RETRIES ]; then
    echo "Could not connect to Elasticsearch on http://${ES_HOST}:9200/"
    break;
  fi
  echo "Waiting for Elasticsearch...";
  retry=$((retry + 1))
  sleep 5;
done;

echo "Connected to Elasticsearch on http://${ES_HOST}:9200/"
ES_STATUS=$(curl -X GET http://${ES_HOST}:9200/)
if [ -n "${ES_STATUS}" ]; then
  echo $ES_STATUS

  ES_HOST=$ES_HOST \
  SQLITE_DB_PATH=$SQLITE_DB_PATH \
  /usr/local/bin/python /app/es_init.py
fi

export ES_HOST=$ES_HOST

exec "$@"
