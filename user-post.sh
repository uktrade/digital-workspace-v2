#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

echo "Running post build script"

echo "Running pip install"
pip install -r requirements.txt

echo "Running npm ci"
npm ci

echo "Renaming .env.ci to .env"
mv ".env.ci" ".env"

cd src

echo "Running collectstatic"
python manage.py collectstatic --settings=config.settings.build --noinput

echo "Renaming .env to .env.ci"
cd ../
mv ".env" ".env.ci"
