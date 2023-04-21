FROM gcr.io/sre-docker-registry/py-node:3.11-18-focal

ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --with dev

COPY . ./

WORKDIR /app/src
