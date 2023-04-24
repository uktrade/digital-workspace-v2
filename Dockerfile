FROM gcr.io/sre-docker-registry/py-node@sha256:2b5b2a2c5ecd8b739c6a7ff1c357eea949af95bd2a1e1601609d56f074e6dff6

ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# RUN pip install poetry
RUN poetry install --with dev

COPY . ./

WORKDIR /app/src
