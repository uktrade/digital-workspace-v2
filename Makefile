.DEFAULT: help

help:
	@echo "Workspace Makefile"
	@echo "------------------"
	@echo
	@echo "make lint"
	@echo "    Runs linters"
	@echo
	@echo "make clean"
	@echo "    Removes compiled artefacts"
	@echo

clean:
	npm run clean
	find . -name '__pycache__' -exec rm -rf {} +

makemigrations:
	docker-compose run --rm wagtail python manage.py makemigrations

migrations:
	docker-compose run --rm wagtail python manage.py makemigrations

empty-migration:
	docker-compose run --rm wagtail python manage.py makemigrations --empty $(app)

checkmigrations:
	docker-compose run --rm --no-deps wagtail python manage.py makemigrations --check

migrate:
	docker-compose run --rm wagtail python manage.py migrate

compilescss:
	docker-compose run --rm wagtail python manage.py compilescss

test:
	docker-compose run --rm --name testrunner wagtail pytest --ignore=selenium_tests --reuse-db $(tests)

test-selenium:
	docker-compose run --rm --name testrunner wagtail pytest selenium_tests

test-all:
	docker-compose run --rm --name testrunner wagtail pytest

coverage:
	docker-compose run --rm --name testrunner wagtail ./scripts/coverage.sh

shell:
	docker-compose run --rm wagtail python manage.py shell

flake8:
	docker-compose run --rm --no-deps wagtail flake8

black:
	docker-compose run --rm --no-deps wagtail black .

check-fixme:
	git --no-pager grep -rni fixme -- ':!./Makefile'

up:
	docker-compose up

down:
	docker-compose down

build:
	docker-compose build

webpack:
	npm run dev

elevate:
	docker-compose run --rm wagtail python manage.py elevate_sso_user_permissions --email=$(email)

collectstatic:
	docker-compose run --rm wagtail python manage.py collectstatic

findstatic:
	docker-compose run --rm wagtail python manage.py findstatic $(app)

bash:
	docker-compose run --rm wagtail bash

all-requirements:
	docker-compose run --rm wagtail pip-compile --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm wagtail pip-compile --output-file requirements/dev.txt requirements.in/dev.in
	docker-compose run --rm wagtail pip-compile --output-file requirements/prod.txt requirements.in/prod.in

upgrade-package:
	docker-compose run --rm wagtail pip-compile --upgrade-package $(package) --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm wagtail pip-compile --upgrade-package $(package) --output-file requirements/dev.txt requirements.in/dev.in
	docker-compose run --rm wagtail pip-compile --upgrade-package $(package) --output-file requirements/prod.txt requirements.in/prod.in

superuser:
	docker-compose run --rm wagtail python manage.py migrate
	echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password', first_name='admin', last_name='test')" | docker-compose run --rm wagtail python manage.py shell

import:
	docker-compose down
	docker-compose up -d
	docker-compose exec wagtail python manage.py migrate
	docker-compose exec wagtail python manage.py add_s3_bucket_assets_to_wagtail
	docker-compose exec wagtail python manage.py import_wordpress
	docker-compose exec wagtail python manage.py create_menus
	docker-compose run --rm wagtail python manage.py create_groups
	echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password')" | docker-compose run --rm wagtail python manage.py shell
	docker-compose stop wagtail
	docker-compose up

restore_test_db:
	docker-compose stop db
	docker-compose up -d db
	dropdb -h localhost -U postgres digital_workspace
	createdb -h localhost -U postgres digital_workspace
	pg_restore -h localhost -U postgres --dbname=digital_workspace --verbose backup_file.backup
	docker-compose exec wagtail python manage.py migrate

import_test:
	docker-compose stop db
	docker-compose up -d db
	dropdb -h localhost -U postgres digital_workspace
	createdb -h localhost -U postgres digital_workspace
	pg_restore -h localhost -U postgres --dbname=digital_workspace --verbose backup_s3_asset_only.backup
	docker-compose exec wagtail python manage.py migrate
	#docker-compose exec wagtail python manage.py add_s3_bucket_assets_to_wagtail
	docker-compose run --rm wagtail python manage.py fixtree
	docker-compose exec wagtail python manage.py import_wordpress
	docker-compose exec wagtail python manage.py create_menus
	docker-compose run --rm wagtail python manage.py create_groups

add_s3_assets:
	docker-compose exec wagtail python manage.py add_s3_bucket_assets_to_wagtail

fixtree:
	docker-compose run --rm wagtail python manage.py fixtree

menus:
	docker-compose run --rm wagtail python manage.py create_menus

index:
	docker-compose run --rm wagtail python manage.py update_index

listlinks:
	docker-compose run --rm wagtail python manage.py list_links

groups:
	docker-compose run --rm wagtail python manage.py create_groups

create_section_homepages:
	docker-compose run --rm wagtail python manage.py create_section_homepages
