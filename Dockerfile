FROM gcr.io/sre-docker-registry/py-node:3.11-18-jammy

ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry
RUN poetry install --with dev

COPY . ./

WORKDIR /app/src
