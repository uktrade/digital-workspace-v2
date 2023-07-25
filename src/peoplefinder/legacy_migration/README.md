# Legacy migration

This folder contains an archive of all the code we used to migrate from the legacy People Finder.

## legacy_models.py
The models that represent the legacy data.

## routers.py
Contains the DB router to make sure the ORM doesn't run migrations on the legacy database, and to make sure queries from the legacy models were directed to the legacy DB.

## migrate_legacy.py
The management command and migration commands for ingesting the legacy data into the new instance.
