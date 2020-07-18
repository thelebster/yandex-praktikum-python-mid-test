#!/bin/sh
set -e

from=1
to=100
MAX_COUNT=$(curl -X GET "https://api.ivi.ru/mobileapi/catalogue/v5/?app_version=870" | jq -r '.count')
until [ "$to" -ge "$MAX_COUNT" ]
do
  rm -rf /tmp/movies.csv
  curl -X GET "https://api.ivi.ru/mobileapi/catalogue/v5/?from=${from}&to=${to}&app_version=870" | \
    jq -r '.result[] | .["file_path"] = .share_link | [.id,.title,.description // "",.file_path // ""] | @csv' \
    > /tmp/movies.csv
  if [ -f /tmp/movies.csv ] || [ -s /tmp/movies.csv ]; then
    sqlite3 /var/sqlite/db/movies.db -separator "," -cmd ".mode csv" ".import /tmp/movies.csv movies" ".quit"
  fi
  from=$((from + 100))
  to=$((to + 100))
done
