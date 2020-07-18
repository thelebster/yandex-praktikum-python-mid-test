#!/bin/sh
set -e

mkdir -p /var/sqlite/db
if [ ! -f /var/sqlite/db/movies.db ]; then
  # Create a new database with a table 'movies'.
  sqlite3 /var/sqlite/db/movies.db -cmd "CREATE TABLE movies (
    id text primary key,
    title text,
    description text,
    file_path text,
    srt_path text
  );" ".quit"

  sqlite3 /var/sqlite/db/movies.db -cmd ".schema" ".quit"

  # Prepare dataset, select only required fields.
  cat /tmp/movies.json | \
    jq -r '.result[] | .["file_path"] = .share_link | [.id,.title,.description // "",.file_path // ""] | @csv' \
    > /tmp/movies.csv

  # Import movies from the csv file.
  sqlite3 /var/sqlite/db/movies.db -separator "," -cmd ".mode csv" ".import /tmp/movies.csv movies" ".quit"
  # Select the 5 first records to be sure.
  sqlite3 /var/sqlite/db/movies.db -cmd "SELECT * FROM movies LIMIT 5;" ".quit"
fi

exec "$@"
