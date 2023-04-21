FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHON_VERSION=3.11
ENV NODE_VERSION=18
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py
ENV POETRY_VIRTUALENVS_CREATE=false

# Install Python & Node
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Install general packages
    git nano \
    curl wget gpg \
    openssh-client \
    tzdata \
    build-essential \
    libpq-dev \
    software-properties-common && \
    # Install python and supporting packages
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-distutils && \
    # set as default Python (to e.g. avoid needing virtualenvs)
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    # Pip
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py && \
    rm get-pip.py && \
    # Install Node
    curl -sL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    # clean apt cache
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry

RUN poetry install --with dev

COPY . ./

WORKDIR /app/src
