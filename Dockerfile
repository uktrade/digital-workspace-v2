FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHON_VERSION=python3.9
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py
ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y \
    ${PYTHON_VERSION} \
    ${PYTHON_VERSION}-dev \
    libpq-dev \
    build-essential \
    python3-pip \
    --no-install-recommends tzdata
RUN rm -rf /usr/bin/python3 && ln -s /usr/bin/${PYTHON_VERSION} /usr/bin/python3 && ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry

RUN poetry install --with dev

COPY . ./

RUN npm ci && npm run build
