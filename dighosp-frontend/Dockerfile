FROM python:3.12-slim as builder
RUN pip install poetry

ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y dist-upgrade && apt-get -y install gcc
RUN mkdir /app
COPY pyproject.toml poetry.lock /app/

RUN cd /app && poetry install --no-interaction --no-ansi --without dev

######

FROM python:3.12-slim as runtime

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=builder /app/ /app/
COPY /dighosp_frontend /app/dighosp_frontend
COPY /services.toml /app/services.toml
COPY --from=assets . /app/assets

CMD gunicorn dighosp_frontend.app:server -b "0.0.0.0:8000" -t ${TIMEOUT:-120} -w ${NUM_WORKERS:-4}
