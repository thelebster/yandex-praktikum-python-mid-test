FROM python:3.7-slim
LABEL maintainer="Anton Lebedev <mailbox@lebster.me>"
WORKDIR /app
RUN apt-get update \
    && apt-get install -y sqlite jq curl
RUN pip install pipenv \
    && pip install gunicorn \
    && pip install gevent
COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt \
    && pip install -r /tmp/requirements.txt
COPY server.py /app/server.py
COPY es_init.py /app/es_init.py
COPY common/movies.json /tmp/
COPY add-movies.sh /
COPY entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
ENV FLASK_APP=${FLASK_APP}
ENV FLASK_ENV=${FLASK_ENV}
ENV GUNICORN_CMD_ARGS=${GUNICORN_CMD_ARGS}
CMD gunicorn -b ${FLASK_HOST}:${FLASK_PORT} ${GUNICORN_CMD_ARGS} server:app
