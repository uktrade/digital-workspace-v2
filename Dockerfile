FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHON_VERSION=3.9
ENV NODE_VERSION=18
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py
ENV POETRY_VIRTUALENVS_CREATE=false

# Install Python & Node
RUN curl -sL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get update && apt-get install -y --no-install-recommends \
    # Install general packages
    git nano \
    curl wget gpg \
    openssh-client \
    tzdata \
    build-essential \
    libpq-dev \
    # Install python and supporting packages
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    # Install Node
    nodejs \
    npm && \
    # Setup python symlinks
    rm -rf /usr/bin/python3 && \
    ln -s /usr/bin/python${PYTHON_VERSION} /usr/bin/python3 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    # clean apt cache
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry

RUN poetry install --with dev

COPY . ./
