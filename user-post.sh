#!/usr/bin/env bash

echo "Running post build script"
pip install -r requirements.txt
npm ci

cd src

python manage.py collectstatic --settings=config.settings.build --noinput
