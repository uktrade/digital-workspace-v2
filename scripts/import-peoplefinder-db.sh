#!/bin/bash

# For this script you will need a SQL dump from a legacy peoplefinder database using
# `pg_dump`. This can come from either a local peoplefinder database or from any of the
# PaaS environments.

set -ex

export PGPASSWORD='postgres'

POSTGRES_HOST="localhost"
POSTGRES_USER="postgres"
DATABASE_NAME="legacy_peoplefinder"

psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "CREATE DATABASE $DATABASE_NAME TEMPLATE template0;"

psql -h $POSTGRES_HOST -U $POSTGRES_USER -f $1 $DATABASE_NAME
