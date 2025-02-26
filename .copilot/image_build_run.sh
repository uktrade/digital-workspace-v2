#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

echo "Running post build script"

echo "Copy .env.ci to .env"
cp ".env.ci" ".env"

cd src

echo "Running collectstatic"
DJANGO_SETTINGS_MODULE=config.settings.build python manage.py collectstatic --noinput

echo "Delete the .env file"
cd ../
rm ".env"
