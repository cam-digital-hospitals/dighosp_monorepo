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

LABEL org.opencontainers.image.title="Digital Hospitals: Discrete-event Simulation \
frontend dashboard"
LABEL org.opencontainers.image.source https://github.com/cam-digital-hospitals/dighosp_monorepo
LABEL org.opencontainers.image.authors "Yin-Chi Chan <ycc39@cam.ac.uk>; \
Rohit Krishnan <rk759@cam.ac.uk>; Anandarup Mukherjee <am2910@cam.ac.uk>"

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=builder /app/ /app/
COPY /dighosp_frontend /app/dighosp_frontend
COPY /services.toml /app/services.toml
COPY --from=assets . /app/assets

CMD gunicorn dighosp_frontend.app:server -b "0.0.0.0:8000" -t ${TIMEOUT:-120} -w ${NUM_WORKERS:-4}
