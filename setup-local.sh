#!/bin/bash

set -ex

virtualenv --python=python3 .venv

source .venv/bin/activate

pip install -r requirements/dev.txt

deactivate
