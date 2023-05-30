# FROM gcr.io/sre-docker-registry/py-node:3.11-18-jammy
ARG UBUNTU_VERSION=jammy
FROM ubuntu:${UBUNTU_VERSION}

ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=18
ARG APT_REPOSITORY="ppa:deadsnakes/ppa"

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py
ENV POETRY_VIRTUALENVS_CREATE=false

# Install base
RUN apt-get update && apt-get install -y --no-install-recommends \
    # General packages
    curl wget \
    # Dev help packages
    git nano \
    # Supporting packages
    openssh-client \
    tzdata \
    gpg gpg-agent \
    # Compilation tools
    build-essential \
    libpq-dev \
    software-properties-common

# Extra repo to install this version of Python on this version of Ubuntu
RUN if [ ! -z "${APT_REPOSITORY}" ]; then \
    add-apt-repository ${APT_REPOSITORY} -y; \
    fi

# Install Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-distutils && \
    # set as default Python (to e.g. avoid needing virtualenvs)
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    # Pip
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py && \
    rm get-pip.py

# Install Node
RUN curl -sL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get install -y --no-install-recommends \
    nodejs

# Tidy up
RUN \
    # Clean apt cache
    rm -rf /var/lib/apt/lists/* \
    # Add pwuser
    adduser pwuser

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry
RUN poetry update
RUN poetry install --with dev

COPY . ./

WORKDIR /app/src
