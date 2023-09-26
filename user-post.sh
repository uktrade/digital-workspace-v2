#!/usr/bin/env bash

echo "Running post build script"

echo "Running pip install"
pip install -r requirements.txt

echo "Running npm ci"
npm ci

echo "Renaming .env.ci to .env"
mv ".env.ci" ".env"

cd src

echo "Running collectstatic"
python manage.py collectstatic --settings=config.settings.test --noinput

echo "Renaming .env to .env.ci"
cd ../
mv ".env" ".env.ci"
