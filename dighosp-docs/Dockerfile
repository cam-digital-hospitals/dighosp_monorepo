FROM python:3.12-slim as builder
RUN pip install poetry

ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y dist-upgrade && apt-get -y install gcc make

WORKDIR /dighosp-docs

COPY ./pyproject.toml /dighosp-docs/pyproject.toml
RUN poetry install --no-interaction --no-ansi

COPY ./source/ /dighosp-docs/source/
COPY ./Makefile /dighosp-docs/Makefile
RUN poetry run make html SPHINXOPTS="-W --keep-going -n"

########################################################

FROM joseluisq/static-web-server
ENV SERVER_HOST=0.0.0.0

COPY --from=builder /dighosp-docs/build/html /public
