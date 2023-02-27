#!/bin/bash

# For this script you will need a cleaned and anonymised pg_dump SQL file
# The file is expected to be in the project root at /dw_dev_friendly.sql

# NB to grab a SQL dump with a minimum number of extraneous records run (from online DB)
#
# pg_dump -O -x -c -T *_historical* -T *logentry -T *auditlog -T *admin_log -T *session -T *chunk* -T file_upload* > digital_workspace.sql
# pg_dump -O -x -c -s -t *_historical* -t *logentry -t *auditlog -t *admin_log -t *session -t *chunk* -t file_upload* >> digital_workspace.sql
#
# now add that to a new DB
# psql -h localhost -U postgres -c "CREATE DATABASE test_dump TEMPLATE template0;"
# psql -h localhost -U postgres -f digital_workspace.sql test_dump
#
# ensure you set that DB in your local settings / .env while you work on this
#
# now truncate the dataset by removing old page revisions etc
# psql -h localhost -U postgres -c "DELETE FROM wagtailcore_pagerevision WHERE id NOT IN ( SELECT live_revision_id FROM wagtailcore_page WHERE live_revision_id IS NOT NULL)"
# psql -h localhost -U postgres -c "DELETE FROM core_historicaldocument"
#
# use the name list to rename everyone, swapping emails and phones as well
# make shell (using shell_plus)
# paste truncate_anonymise.py.cli code into shell and run it - if errors try re-running it
#
# generate the data dump file
# pg_dump -h localhost -U postgres test_dump > dw_dev_friendly.sql



set -e

export PGPASSWORD='postgres'

POSTGRES_HOST="localhost"
POSTGRES_USER="postgres"
DATABASE_NAME="digital_workspace"

FILE=./dw_dev_friendly.sql
if test -f "$FILE"
then

    echo "! NOTE: Despite the name, the content you're uploading is still protected; be careful not to share anything outside the organisation"
    echo
    echo "This will completely replace your local dev database"
    read -p "Do you want to continue? [yN]" -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        docker-compose run --rm -p "5432:5432" -d db
        sleep 2

        psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "DROP DATABASE $DATABASE_NAME;"
        psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "CREATE DATABASE $DATABASE_NAME TEMPLATE template0;"

        psql -h $POSTGRES_HOST -U $POSTGRES_USER -f dw_dev_friendly.sql $DATABASE_NAME

        docker-compose kill db

        echo "Done. Since your DB has been overwritten you'll need to auth again and then make new superuser records to access the admin..."
    else
        echo "OK, cancelling withought doing anything."
    fi

else
    echo "Data dump file not found."
    exit 1
fi
