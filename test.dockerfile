FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py

RUN apt-get update
RUN apt-get install -y \
    python3.9-dev \
    libpq-dev \
    build-essential \
    python3-pip \
    --no-install-recommends tzdata

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry
RUN poetry env use /usr/bin/python3.9
RUN poetry install --with dev
RUN poetry run playwright install-deps
RUN poetry run playwright install chrome

COPY . ./
RUN cp .env.ci .env
