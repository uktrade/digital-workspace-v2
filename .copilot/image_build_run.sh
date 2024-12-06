#!/usr/bin/env bash

# Exit early if something goes wrong
set -e
export DJANGO_SETTINGS_MODULE=config.settings.build

echo "Running post build script"

echo "Renaming .env.ci to .env"
mv ".env.ci" ".env"

cd src

echo "Running collectstatic"
python manage.py collectstatic --noinput

echo "Renaming .env to .env.ci"
cd ../
mv ".env" ".env.ci"
