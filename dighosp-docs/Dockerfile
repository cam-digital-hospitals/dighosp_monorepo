FROM python:3.12-slim as builder
RUN pip install poetry

ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y dist-upgrade && apt-get -y install gcc make

WORKDIR /docs

COPY . .
RUN poetry install  --no-interaction --no-ansi
RUN poetry run make html

########################################################

FROM joseluisq/static-web-server
COPY --from=builder /docs/build/html /public

EXPOSE 80
