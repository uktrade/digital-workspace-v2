#!/bin/bash

# For this script you will need a cleaned and anonymised pg_dump SQL file
# The file is expected to be in the project root at /dw_dev_friendly.sql


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



# To grab a SQL dump with a minimum number of extraneous records run all the following steps:
#
# (from online DB)
# pg_dump -O -x -c -T *_historical* -T *logentry -T *auditlog -T *admin_log -T *session -T *chunk* -T file_upload* > digital_workspace.sql
# pg_dump -O -x -c -s -t *_historical* -t *logentry -t *auditlog -t *admin_log -t *session -t *chunk* -t file_upload* >> digital_workspace.sql
#
# now add that to a new DB on your local
# docker-compose run --rm -p "5432:5432" -d db
# export PGPASSWORD='postgres'
# psql -h localhost -U postgres -c "DROP DATABASE test_dump;"
# psql -h localhost -U postgres -c "CREATE DATABASE test_dump TEMPLATE template0;"
# psql -h localhost -U postgres -t test_dump -f digital_workspace.sql
#
# now truncate the dataset by removing old page revisions etc
# psql -h localhost -U postgres -t test_dump -c "DELETE FROM wagtailcore_revision WHERE id NOT IN ((SELECT live_revision_id FROM wagtailcore_page WHERE live_revision_id IS NOT NULL) UNION (SELECT latest_revision_id FROM wagtailcore_page WHERE latest_revision_id IS NOT NULL))"
# docker-compose kill db
#
# ensure you set your local .env to use test_dump DB while ytou work on this, and update settings to ignore indexing by having AUTO_UPDATE=False in the wagtail backend settings
# wagtail now maintains an index of linked docs, images etc, but it'll be out of date - update it
# make bash
# python manage.py rebuild_references_index
#
# use the name lists to lose a load of people, rename everyone left, swapping emails and phones as well, then remove unused assets from the DB
# make shell (using shell_plus)
# paste truncate_anonymise.py.cli code into shell (probably best done part by part) and run it - if errors try re-running it
#
# You should be left with 3 linked_xxx.txt files containing filenames of images, docs and media that should be copied from the Prod S3 bucket to the Dev one (and/or others) - they have to be copied locally before being uploaded
# first copy them locally
# mkdir /tmp/files
# while read -r line; do aws s3 cp s3://$prod_bucket/$line /tmp/files/$line --profile dit-intranet-prod-s3; done < linked_media.txt
# while read -r line; do aws s3 cp s3://$prod_bucket/$line /tmp/files/$line --profile dit-intranet-prod-s3; done < linked_docs.txt
# while read -r line; do aws s3 cp s3://$prod_bucket/$line /tmp/files/$line --profile dit-intranet-prod-s3; done < linked_images.txt
# now copy them back up
# aws s3 sync /tmp/files/ s3://$dev_bucket/ --profile dit-intranet-dev-s3
#
# generate the data dump file
# pg_dump -h localhost -U postgres test_dump > dw_dev_friendly.sql
#
# Reset your .env file to use the right DB, and reset your AUTO_UPDATE setting, then run this script
