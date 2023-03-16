FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=python3.9
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py
ENV POETRY_VIRTUALENVS_PATH=~/.venvs/

RUN apt-get update
RUN apt-get install -y \
    $PYTHON_VERSION-dev \
    libpq-dev \
    build-essential \
    python3-pip \
    --no-install-recommends tzdata

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry
RUN poetry env use $(which $PYTHON_VERSION)
RUN poetry install --with dev
RUN poetry run playwright install-deps
RUN poetry run playwright install

COPY . ./
RUN cp .env.ci .env
