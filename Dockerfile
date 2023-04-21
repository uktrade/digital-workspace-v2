FROM gcr.io/sre-docker-registry/py-node:3.11-18-focal

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py
ENV POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock ./

RUN poetry install --with dev -vvv

COPY . ./
WORKDIR /app/src
