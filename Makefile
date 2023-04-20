SHELL := /bin/sh

#
# Container management
#

build:
	DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 BUILDKIT_INLINE_CACHE=1 docker-compose build

build-all:
	DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 BUILDKIT_INLINE_CACHE=1 docker-compose --profile playwright build

up:
	docker-compose up

up-all:
	docker-compose --profile playwright up -d

down:
	docker-compose down

down-all:
	docker-compose --profile playwright down

#
# Linting
#

check:
	docker-compose run --rm --no-deps wagtail black --check .
	docker-compose run --rm --no-deps wagtail ruff check .
	docker-compose run --rm --no-deps wagtail djlint --check .
	! git --no-pager grep -rni fixme -- ':!./Makefile' ':!./.circleci/config.yml'

fix:
	docker-compose run --rm --no-deps wagtail black .
	docker-compose run --rm --no-deps wagtail ruff check --fix .
	docker-compose run --rm --no-deps wagtail djlint --reformat .

#
# Dev utility
#

wagtail = docker-compose run --rm wagtail
chown = $(wagtail) chown $(shell id -u):$(shell id -g)

shell:
	$(wagtail) python manage.py shell_plus

bash:
	$(wagtail) bash

psql:
	PGPASSWORD='postgres' psql -h localhost -U postgres

requirements:
	$(wagtail) poetry export --without-hashes --output requirements.txt

clean:
	npm run clean
	find . -name '__pycache__' -exec rm -rf {} +

first-use:
	docker-compose --profile playwright down
	make migrate
	make data-countries
	make menus
	make create_section_homepages
	make wagtail-groups
	make pf-groups
	make superuser
	docker-compose up

local-setup:
	poetry install
	npm install

dump-db:
	pg_dump digital_workspace -U postgres -h localhost -p 5432 -O -x -c -f dw.dump

superuser:
	$(wagtail) python manage.py shell --command="from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password', first_name='admin', last_name='test')"

#
# Django
#

makemigrations:
	$(wagtail) python manage.py makemigrations
	$(chown) */migrations/*

empty-migration:
	$(wagtail) python manage.py makemigrations --empty $(app)
	$(chown) */migrations/*

checkmigrations:
	$(wagtail) python manage.py makemigrations --check

migrate:
	$(wagtail) python manage.py migrate

collectstatic:
	$(wagtail) python manage.py collectstatic

findstatic:
	$(wagtail) python manage.py findstatic $(app)

fixtree:
	$(wagtail) python manage.py fixtree

#
# Testing
#

test:
	docker-compose run --rm --name testrunner wagtail pytest -m "not e2e" --reuse-db $(tests)

test-e2e: up-all
	docker-compose exec playwright poetry run pytest -m "e2e"
	docker-compose stop playwright

test-all:
	docker-compose run --rm --name testrunner wagtail pytest

coverage:
	docker-compose run --rm --name testrunner wagtail ./scripts/coverage.sh

e2e-codegen:
	cp .env .env.orig
	cp .env.ci .env
	docker-compose stop wagtail
	docker-compose run --rm -d -p 8000:8000 --env DJANGO_SETTINGS_MODULE=config.settings.test --name wagtail-test-server wagtail
	sleep 5
	poetry run playwright codegen http://localhost:8000
	mv .env.orig .env
	docker stop wagtail-test-server

#
# NPM
#

compilescss:
	$(wagtail) python manage.py compilescss

webpack:
	npm run dev

#
# Application-specific
#

elevate:
	$(wagtail) python manage.py elevate_sso_user_permissions --email=$(email)

menus:
	$(wagtail) python manage.py create_menus

index:
	$(wagtail) python manage.py update_index

listlinks:
	$(wagtail) python manage.py list_links

wagtail-groups:
	$(wagtail) python manage.py create_groups

pf-groups:
	$(wagtail) python manage.py create_people_finder_groups

create_section_homepages:
	$(wagtail) python manage.py create_section_homepages

setup_v2_user:
	$(wagtail) python manage.py setup_v2_user $(email)

data-countries:
	$(wagtail) python manage.py loaddata countries.json
