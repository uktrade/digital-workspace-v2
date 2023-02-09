SHELL := /bin/bash

clean:
	npm run clean
	find . -name '__pycache__' -exec rm -rf {} +

wagtail = docker-compose run --rm wagtail
chown = $(wagtail) chown $(shell id -u):$(shell id -g)

makemigrations:
	$(wagtail) python manage.py makemigrations
	$(chown) */migrations/*

migrations:
	$(wagtail) python manage.py makemigrations
	$(chown) */migrations/*

empty-migration:
	$(wagtail) python manage.py makemigrations --empty $(app)
	$(chown) */migrations/*

checkmigrations:
	docker-compose run --rm --no-deps wagtail python manage.py makemigrations --check

migrate:
	$(wagtail) python manage.py migrate

compilescss:
	$(wagtail) python manage.py compilescss

test:
	docker-compose run --rm --name testrunner wagtail pytest --ignore=selenium_tests --reuse-db $(tests) 

test-selenium:
	docker-compose run --rm --name testrunner wagtail pytest selenium_tests

test-all:
	docker-compose run --rm --name testrunner wagtail pytest

coverage:
	docker-compose run --rm --name testrunner wagtail ./scripts/coverage.sh

shell:
	$(wagtail) python manage.py shell

flake8:
	docker-compose run --rm --no-deps wagtail flake8

black-check:
	docker-compose run --rm --no-deps wagtail black --check .

black:
	docker-compose run --rm --no-deps wagtail black .

isort-check:
	docker-compose run --rm --no-deps wagtail isort --check .

isort:
	docker-compose run --rm --no-deps wagtail isort .

check-fixme:
	! git --no-pager grep -rni fixme -- ':!./Makefile' ':!./.circleci/config.yml'

up:
	docker-compose up

down:
	docker-compose down

build:
	docker-compose build

webpack:
	npm run dev

elevate:
	$(wagtail) python manage.py elevate_sso_user_permissions --email=$(email)

collectstatic:
	$(wagtail) python manage.py collectstatic

findstatic:
	$(wagtail) python manage.py findstatic $(app)

bash:
	$(wagtail) bash

requirements:
	$(wagtail) poetry export --without-hashes --output requirements.txt

superuser:
	$(wagtail) python manage.py shell --command="from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password', first_name='admin', last_name='test')"

fixtree:
	$(wagtail) python manage.py fixtree

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

first-use:
	docker-compose down
	make migrate
	make data-countries
	make menus
	make create_section_homepages
	make wagtail-groups
	make pf-groups
	make superuser
	docker-compose up

setup_v2_user:
	$(wagtail) python manage.py setup_v2_user $(email)

# Data
data-countries:
	$(wagtail) python manage.py loaddata countries.json

local-setup:
	poetry install
	npm install
