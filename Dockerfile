FROM gcr.io/sre-docker-registry/py-node:3.11-18-focal

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --with dev

COPY . ./

WORKDIR /app/src
