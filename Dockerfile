FROM python:3.9-buster

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py

ADD . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements/dev.txt
