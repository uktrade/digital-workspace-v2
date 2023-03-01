SHELL := /bin/bash

APPLICATION_NAME="Digital Workspace"

# Colour coding for output
COLOUR_NONE=\033[0m
COLOUR_GREEN=\033[32;01m
COLOUR_YELLOW=\033[33;01m
COLOUR_RED='\033[0;31m'


help:
	@echo -e "$(COLOUR_GREEN)|--- $(APPLICATION_NAME) ---|$(COLOUR_NONE)"
	@echo -e "$(COLOUR_YELLOW)make clean$(COLOUR_NONE) : Clean up python cache and webpack assets"
	@echo -e "$(COLOUR_YELLOW)make makemigrations$(COLOUR_NONE) or $(COLOUR_YELLOW)make migrations$(COLOUR_NONE) : Run Django makemigrations command"
	@echo -e "$(COLOUR_YELLOW)make empty-migration$(COLOUR_NONE) : Run Django makemigrations command with `--empty` flag"
	@echo -e "$(COLOUR_YELLOW)make checkmigrations$(COLOUR_NONE) : Run Django makemigrations command with `--check` flag"
	@echo -e "$(COLOUR_YELLOW)make migrate$(COLOUR_NONE) : Run Django migrate command"
	@echo -e "$(COLOUR_YELLOW)make compilescss$(COLOUR_NONE) : Run Django compilescss command"
	@echo -e "$(COLOUR_YELLOW)make test$(COLOUR_NONE) : Run tests with pytest"
	@echo -e "$(COLOUR_YELLOW)test-selenium$(COLOUR_NONE) : Run selenioum tests with pytest"
	@echo -e "$(COLOUR_YELLOW)test-all$(COLOUR_NONE) : Run all tests with pytest"
	@echo -e "$(COLOUR_YELLOW)coverage$(COLOUR_NONE) : Run tests with pytest and generate coverage report"
	@echo -e "$(COLOUR_YELLOW)shell$(COLOUR_NONE) : Open a Django shell"
	@echo -e "$(COLOUR_YELLOW)flake8$(COLOUR_NONE) : Run flake8"
	@echo -e "$(COLOUR_YELLOW)black-check$(COLOUR_NONE) : Run black checks"
	@echo -e "$(COLOUR_YELLOW)black$(COLOUR_NONE) : Run black formatting"
	@echo -e "$(COLOUR_YELLOW)isort-check$(COLOUR_NONE) : Run isort checks"
	@echo -e "$(COLOUR_YELLOW)isort$(COLOUR_NONE) : Run isort formatting"
	@echo -e "$(COLOUR_YELLOW)check-fixme$(COLOUR_NONE) : Check for fixme comments"
	@echo -e "$(COLOUR_YELLOW)up$(COLOUR_NONE) : Start the docker containers"
	@echo -e "$(COLOUR_YELLOW)down$(COLOUR_NONE) : Stop the docker containers"
	@echo -e "$(COLOUR_YELLOW)build$(COLOUR_NONE) : Build the docker containers"
	@echo -e "$(COLOUR_YELLOW)webpack$(COLOUR_NONE) : Run webpack"
	@echo -e "$(COLOUR_YELLOW)elevate --email=someone@example.com$(COLOUR_NONE) : Elevate the permissions for a given email"
	@echo -e "$(COLOUR_YELLOW)collectstatic$(COLOUR_NONE) : Run the Django collectstatic command"
	@echo -e "$(COLOUR_YELLOW)findstatic$(COLOUR_NONE) : Run the Django findstatic command"
	@echo -e "$(COLOUR_YELLOW)bash$(COLOUR_NONE) : Run bash in the wagtail container"
	@echo -e "$(COLOUR_YELLOW)requirements$(COLOUR_NONE) : Export the requirements to requirements.txt"
	@echo -e "$(COLOUR_YELLOW)superuser$(COLOUR_NONE) : Create a superuser"
	@echo -e "$(COLOUR_YELLOW)fixtree$(COLOUR_NONE) : Fix the tree structure of the pages"
	@echo -e "$(COLOUR_YELLOW)menus$(COLOUR_NONE) : Create the menus"
	@echo -e "$(COLOUR_YELLOW)index$(COLOUR_NONE) : Reindex the search"
	@echo -e "$(COLOUR_YELLOW)listlinks$(COLOUR_NONE) : List all the links in the site"
	@echo -e "$(COLOUR_YELLOW)wagtail-groups$(COLOUR_NONE) : Create the wagtail groups"
	@echo -e "$(COLOUR_YELLOW)pf-groups$(COLOUR_NONE) : Create the pf groups"
	@echo -e "$(COLOUR_YELLOW)create_section_homepages$(COLOUR_NONE) : Create the section homepages"
	@echo -e "$(COLOUR_YELLOW)first-use$(COLOUR_NONE) : Run the first use commands"
	@echo -e "$(COLOUR_YELLOW)setup_v2_user --email=someone@example.com$(COLOUR_NONE) : Set up a v2 user with a given email"
	@echo -e "$(COLOUR_YELLOW)data-countries$(COLOUR_NONE) : Import the countries data"
	@echo -e "$(COLOUR_YELLOW)local-setup$(COLOUR_NONE) : Run the local setup commands"

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
	docker-compose run --rm --name testrunner wagtail pytest -m "not selenium" --reuse-db $(tests)

test-selenium:
	docker-compose run --rm --name testrunner wagtail pytest -m "selenium"

test-all:
	docker-compose run --rm --name testrunner wagtail pytest

coverage:
	docker-compose run --rm --name testrunner wagtail ./scripts/coverage.sh

shell:
	$(wagtail) python manage.py shell_plus

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
