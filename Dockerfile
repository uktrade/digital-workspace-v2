FROM sre-docker-registry/py-node:3.11-18-jammy

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --with dev

COPY . ./

WORKDIR /app/src
