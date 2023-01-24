#!/bin/bash

set -ex

# python
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements/dev.txt

deactivate

# node
npm install
