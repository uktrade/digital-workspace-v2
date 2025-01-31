#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

echo "Running post build script"

echo "Renaming .env.ci to .env"
mv ".env.ci" ".env"

cd src

export DJANGO_SETTINGS_MODULE=config.settings.build
echo "Running collectstatic"
python manage.py collectstatic --noinput

echo "Renaming .env to .env.ci"
cd ../
mv ".env" ".env.ci"
