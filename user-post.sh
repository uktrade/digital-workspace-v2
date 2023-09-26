#!/usr/bin/env bash

echo "Running post build script"
pip install -r requirements.txt
npm ci

echo "Renaming .env.ci to .env"
ls -al
mv ".env.ci" ".env"
ls -al

cd src

python manage.py collectstatic --settings=config.settings.test --noinput

echo "Renaming .env to .env.ci"
cd ../
ls -al
mv ".env" ".env.ci"
ls -al
