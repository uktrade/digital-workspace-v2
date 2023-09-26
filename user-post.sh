#!/usr/bin/env bash

echo "Running post build script"
pip install -r requirements.txt
npm ci

mv ".env.ci" ".env"

cd src

python manage.py collectstatic --settings=config.settings.test --noinput

mv ".env" ".env.ci"
