SHELL := /bin/sh

APPLICATION_NAME="Digital Workspace"

# Colour coding for output
CLR__=\033[0m
CLR_G=\033[32;01m
CLR_Y=\033[33;01m
CLR_R='\033[0;31m'

help:
	@echo "$(CLR_G)|--- $(APPLICATION_NAME) ---|$(CLR__)"
	@echo "\n$(CLR_G)Container management$(CLR__)"
	@echo "$(CLR_Y)build$(CLR__) : Build the app's docker containers"
	@echo "$(CLR_Y)up$(CLR__) : Start the app's docker containers"
	@echo "$(CLR_Y)down$(CLR__) : Stop the app's docker containers"
	@echo "$(CLR_Y)build-all$(CLR__) : Build all docker containers (inc. testrunner)"
	@echo "$(CLR_Y)up-all$(CLR__) : Start all docker containers in the background (inc. testrunner)"
	@echo "$(CLR_Y)down-all$(CLR__) : Stop all docker containers (inc. testrunner)"
	@echo "\n$(CLR_G)Linting$(CLR__)"
	@echo "$(CLR_Y)check$(CLR__) : Run black, ruff and djlint in 'check' modes, and scan for 'fixme' comments"
	@echo "$(CLR_Y)fix$(CLR__) : Run black, ruff and djlint in 'fix' modes"
	@echo "\n$(CLR_G)Dev utility$(CLR__)"
	@echo "$(CLR_Y)shell$(CLR__) : Open a Django shell"
	@echo "$(CLR_Y)bash$(CLR__) : Run bash in the wagtail container"
	@echo "$(CLR_Y)psql$(CLR__) : Run the psql shell against the DB container"
	@echo "$(CLR_Y)requirements$(CLR__) : Export the requirements to requirements.txt"
	@echo "$(CLR_Y)clean$(CLR__) : Clean up python cache and webpack assets"
	@echo "$(CLR_Y)local-setup$(CLR__) : Run the local setup commands for the host machine interpreter"
	@echo "$(CLR_Y)dump-db$(CLR__) : Export the database to a local file"
	@echo "$(CLR_Y)reset-db$(CLR__) : Reset the database"
	@echo "$(CLR_Y)first-use$(CLR__) : Run the first use commands to set up the project for development"
	@echo "$(CLR_Y)superuser$(CLR__) : Create a superuser"
	@echo "\n$(CLR_G)Django$(CLR__)"
	@echo "$(CLR_Y)makemigrations$(CLR__) : Run Django makemigrations command"
	@echo "$(CLR_Y)empty-migration --app=???$(CLR__) : Run Django makemigrations command with `--empty` flag"
	@echo "$(CLR_Y)checkmigrations$(CLR__) : Run Django makemigrations command with `--check` flag"
	@echo "$(CLR_Y)migrate$(CLR__) : Run Django migrate command"
	@echo "$(CLR_Y)collectstatic$(CLR__) : Run the Django collectstatic command"
	@echo "$(CLR_Y)findstatic$(CLR__) : Run the Django findstatic command"
	@echo "$(CLR_Y)fixtree$(CLR__) : Fix the tree structure of the pages"
	@echo "\n$(CLR_G)Testing$(CLR__)"
	@echo "$(CLR_Y)test$(CLR__) : Run (only) unit tests with pytest"
	@echo "$(CLR_Y)test-e2e$(CLR__) : Run (only) end to end tests with playwright and pytest"
	@echo "$(CLR_Y)test-all$(CLR__) : Run all tests with pytest"
	@echo "$(CLR_Y)coverage$(CLR__) : Run tests with pytest and generate coverage report"
	@echo "$(CLR_Y)e2e-codegen$(CLR__) : Set up local environment and run Playwright's interactive test recorder"
	@echo "\n$(CLR_G)Front end$(CLR__)"
	@echo "$(CLR_Y)compilescss$(CLR__) : Run Django compilescss command"
	@echo "$(CLR_Y)webpack$(CLR__) : Run webpack"
	@echo "\n$(CLR_G)Application-specific$(CLR__)"
	@echo "$(CLR_Y)elevate --email=someone@example.com$(CLR__) : Elevate the permissions for a given email"
	@echo "$(CLR_Y)menus$(CLR__) : Create the menus"
	@echo "$(CLR_Y)index$(CLR__) : Reindex the search"
	@echo "$(CLR_Y)listlinks$(CLR__) : List all the links in the site"
	@echo "$(CLR_Y)wagtail-groups$(CLR__) : Create the wagtail groups"
	@echo "$(CLR_Y)pf-groups$(CLR__) : Create the pf groups"
	@echo "$(CLR_Y)create_section_homepages$(CLR__) : Create the section homepages"
	@echo "$(CLR_Y)setup_v2_user --email=someone@example.com$(CLR__) : Create/enable Django user with v2 search flag"
	@echo "$(CLR_Y)data-countries$(CLR__) : Import the countries data"


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

# Run a command in a new container
wagtail-run = docker-compose run --rm wagtail
# Run a command in a new container (don't start dependencies)
wagtail-run-no-deps = $(wagtail-run-no-deps)
# Run a command in an existing container
wagtail-exec = docker-compose exec wagtail
# Run tests in a new container named 'testrunner'
testrunner = docker-compose run --rm --name testrunner wagtail

#
# Linting
#

check:
	$(wagtail-run-no-deps) black --check .
	$(wagtail-run-no-deps) ruff check .
	$(wagtail-run-no-deps) djlint --check .
	! git --no-pager grep -rni fixme -- ':!./Makefile' ':!./.circleci/config.yml'

fix:
	$(wagtail-run-no-deps) black .
	$(wagtail-run-no-deps) ruff check --fix .
	$(wagtail-run-no-deps) djlint --reformat .

#
# Dev utility
#

shell:
	$(wagtail-exec) python manage.py shell_plus

bash:
	$(wagtail-exec) bash

psql:
	PGPASSWORD='postgres' psql -h localhost -U postgres

requirements:
	$(wagtail-exec) poetry export --without-hashes --output requirements.txt

clean:
	npm run clean
	find . -name '__pycache__' -exec rm -rf {} +

local-setup:
	poetry install -G dev
	npm install

dump-db:
	pg_dump digital_workspace -U postgres -h localhost -p 5432 -O -x -c -f dw.dump

reset-db:
	docker-compose kill db
	rm -rf ./.db/
	docker-compose start db

first-use:
	docker-compose --profile playwright down
	make reset-db
	make migrate
	make data-countries
	make menus
	make create_section_homepages
	make wagtail-groups
	make pf-groups
	make superuser
	docker-compose up
	make local-setup

superuser:
	$(wagtail-exec) python manage.py shell --command="from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password', first_name='admin', last_name='test')"

#
# Django
#

chown = $(wagtail-exec) chown $(shell id -u):$(shell id -g)

makemigrations:
	$(wagtail-exec) python manage.py makemigrations
	$(chown) */migrations/*

empty-migration:
	$(wagtail-exec) python manage.py makemigrations --empty $(app)
	$(chown) */migrations/*

checkmigrations:
	$(wagtail-run) python manage.py makemigrations --check

migrate:
	$(wagtail-exec) python manage.py migrate

collectstatic:
	$(wagtail-exec) python manage.py collectstatic

findstatic:
	$(wagtail-exec) python manage.py findstatic $(app)

fixtree:
	$(wagtail-exec) python manage.py fixtree

#
# Testing
#

test:
	$(testrunner) pytest -m "not e2e" --reuse-db $(tests)

test-e2e: up-all
	docker-compose exec playwright poetry run pytest -m "e2e"
	docker-compose stop playwright

test-all:
	$(testrunner) pytest

coverage:
	$(testrunner) ./scripts/coverage.sh

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
# Front end
#

compilescss:
	$(wagtail-exec) python manage.py compilescss

webpack:
	npm run dev

#
# Application-specific
#

elevate:
	$(wagtail-exec) python manage.py elevate_sso_user_permissions --email=$(email)

menus:
	$(wagtail-exec) python manage.py create_menus

index:
	$(wagtail-exec) python manage.py update_index

listlinks:
	$(wagtail-exec) python manage.py list_links

wagtail-groups:
	$(wagtail-exec) python manage.py create_groups

pf-groups:
	$(wagtail-exec) python manage.py create_people_finder_groups

create_section_homepages:
	$(wagtail-exec) python manage.py create_section_homepages

setup_v2_user:
	$(wagtail-exec) python manage.py setup_v2_user $(email)

data-countries:
	$(wagtail-exec) python manage.py loaddata countries.json
