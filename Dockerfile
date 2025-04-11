FROM python:3.13-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry==2.1.2

COPY poetry.lock pyproject.toml /app/

RUN poetry install --with dev

COPY . /app/

WORKDIR /app/src
