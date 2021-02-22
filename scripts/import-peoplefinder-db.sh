#!/bin/bash

# This script is a WIP and is here as a reminder of how to import a
# database dump into the digital workspace database.

set -ex

export PGPASSWORD='postgres'

POSTGRES_HOST="localhost"
POSTGRES_USER="postgres"
DATABASE_NAME="legacy_peoplefinder"

psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "CREATE DATABASE $DATABASE_NAME TEMPLATE template0;"

psql -h $POSTGRES_HOST -U $POSTGRES_USER -f peoplefinder-dev.sql $DATABASE_NAME
