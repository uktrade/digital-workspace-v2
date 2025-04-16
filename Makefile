SHELL := /bin/sh

APPLICATION_NAME="Digital Workspace"

.PHONY: help setup

help: # List commands and their descriptions
	@grep -E '^[a-zA-Z0-9_-]+: # .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ": # "; printf "\n\033[93;01m%-30s %-30s\033[0m\n\n", "Command", "Description"}; {split($$1,a,":"); printf "\033[96m%-30s\033[0m \033[92m%s\033[0m\n", a[1], $$2}'

#
# Makefile variables
#

# Run a command in a new container
wagtail-run = docker compose run --rm wagtail
# Run a command in an existing container
wagtail-exec = docker compose exec wagtail
# Run on existing container if available otherwise a new one
wagtail := ${if $(shell docker ps -q -f name=wagtail),$(wagtail-exec),$(wagtail-run)}

# Run a command in a new container (without dependencies)
wagtail-run-no-deps = docker compose run --rm --no-deps wagtail
# Run on existing container if available otherwise a new one (without dependencies)
wagtail-no-deps := ${if $(shell docker ps -q -f name=wagtail),$(wagtail-exec),$(wagtail-run-no-deps)}

# Run tests in a new container named 'testrunner'
testrunner = docker compose run --rm --name testrunner wagtail

chown = $(wagtail-exec) chown $(shell id -u):$(shell id -g)


#
# Container management
#

build: # Build the app's docker containers
	DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 BUILDKIT_INLINE_CACHE=1 docker compose build

build-all: # Build all docker containers (inc. testrunner, opensearch dash)
	DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 BUILDKIT_INLINE_CACHE=1 docker compose --profile playwright --profile opensearch build

up: # Start the app's docker containers
	docker compose up

up-all: # Start all docker containers in the background (inc. testrunner, opensearch dash)
	docker compose --profile playwright --profile opensearch --profile celery-beat up -d

down: # Stop the app's docker containers
	docker compose down

down-all: # Stop all docker containers (inc. testrunner, opensearch dash)
	docker compose --profile playwright --profile opensearch --profile celery-beat down

refresh-web: # Refresh the web container
	make build
	docker compose stop wagtail
	docker compose up -d wagtail

run-prod: # Bring up the docker containers in a "like prod" setup
	docker compose stop wagtail
	$(wagtail-run) --service-ports web granian --interface wsgi config.wsgi:application --workers 1 --host 0.0.0.0 --port 8000

#
# Linting
#

check: # Run black, ruff and djlint in 'check' modes, and scan for 'fixme' comments
	$(wagtail-no-deps) black --check .
	$(wagtail-no-deps) ruff check .
	$(wagtail-no-deps) djlint --check .
	! git --no-pager grep -rni fixme -- ':!./Makefile' ':!./.circleci/config.yml'

fix: # Run black, ruff and djlint in 'fix' modes
	$(wagtail-no-deps) black .
	$(wagtail-no-deps) ruff check --fix .
	$(wagtail-no-deps) djlint --reformat .

#
# Dev utility
#

shell: # Open a Django shell in the wagtail container
	$(wagtail) python manage.py shell_plus

bash: # Run bash in the wagtail container
	$(wagtail) bash

clean: # Clean up python cache and webpack assets
	npm run clean
	find . -name '__pycache__' -exec rm -rf {} +

local-setup: # Run the local setup commands for the host machine interpreter
	poetry install --with dev
	npm install
	npm run build

db-shell: # Run the psql shell against the DB container
	PGPASSWORD='postgres' psql -h localhost -U postgres digital_workspace

db-dump: # Export the database to a local file
	pg_dump digital_workspace -U postgres -h localhost -p 5432 -O -x -c -f dw.dump

db-from-dump: # Create the database from a local file
	PGPASSWORD='postgres' psql -h localhost -U postgres digital_workspace -f dw.dump

db-reset: # Reset the database
	docker compose stop db
	rm -rf ./.db/
	docker compose up -d db

setup: # Run the first use commands to set up the project for development
	npm install
	npm run build
	docker compose --profile playwright --profile opensearch --profile celery-beat down
	make build
	make db-reset
	sleep 3
	make migrate
	make data-countries
	make menus
	make create-section-homepages
	make wagtail-groups
	make pf-groups
	make pf-test-teams
	make ingest-uk-staff-locations
	make superuser
	make index
	make up

superuser: # Create a superuser
	$(wagtail) python manage.py shell --command="from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password', first_name='admin', last_name='test')"

su-all: # Makes all users a superuser
	$(wagtail) python manage.py shell --command="from django.contrib.auth import get_user_model; get_user_model().objects.all().update(is_superuser=True, is_staff=True)"

#
# Django
#

migrations: # Run Django makemigrations command
	$(wagtail) python manage.py makemigrations

empty-migration: # Run Django makemigrations command with `--empty` flag
	$(wagtail) python manage.py makemigrations --empty $(app)

checkmigrations: # Run Django makemigrations command with `--check` flag
	$(wagtail) python manage.py makemigrations --check

migrate: # Run Django migrate command
	$(wagtail) python manage.py migrate

collectstatic: # Run the Django collectstatic command
	$(wagtail) python manage.py collectstatic

findstatic: # Run the Django findstatic command
	$(wagtail) python manage.py findstatic $(app)

fixtree: # Fix the tree structure of the pages
	$(wagtail) python manage.py fixtree

#
# Testing
#

test: # Run (only) unit tests with pytest
	$(testrunner) pytest -m "not e2e" --reuse-db $(tests)

test-fresh: # Run (only) unit tests with pytest using a clean database
	$(testrunner) pytest -m "not e2e" $(tests)

test-e2e: # Run (only) end to end tests with playwright and pytest
	make up-all
	docker compose exec playwright poetry run pytest -m "e2e" $(tests)
	docker compose stop playwright

test-all: # Run all tests with pytest
	$(testrunner) pytest

coverage: # Run tests with pytest and generate coverage report
	$(testrunner) ../scripts/coverage.sh

e2e-codegen: # Set up local environment and run Playwright's interactive test recorder
	if [ ! -f .env.orig ]; then cp .env .env.orig; echo "backed up .env to .env.orig"; else echo "!! found existing .env.orig backup"; fi
	cp .env.ci .env
	docker compose stop wagtail
	docker compose run --rm -d -p 8000:8000 --env DJANGO_SETTINGS_MODULE=config.settings.test --name wagtail-test-server wagtail
	poetry run playwright install chromium
	sleep 5
	poetry run playwright codegen http://localhost:8000
	mv .env.orig .env
	docker stop wagtail-test-server

#
# Front end
#

compilescss: # Run Django compilescss command
	$(wagtail) python manage.py compilescss

webpack: # Run webpack
	npm run dev

#
# Application-specific
#

elevate: # Elevate the permissions for a given email
	$(wagtail) python manage.py elevate_sso_user_permissions --email=$(email)

menus: # Create the menus
	$(wagtail) python manage.py create_menus

index: # Reindex the search
	$(wagtail) python manage.py update_index

listlinks: # List all the links in the site
	$(wagtail) python manage.py list_links

wagtail-groups: # Create the wagtail groups
	$(wagtail) python manage.py create_groups

pf-groups: # Create the pf groups
	$(wagtail) python manage.py create_people_finder_groups

pf-test-teams: # Add test data for peoplefinder teams (suitable for local dev)
	$(wagtail) python manage.py create_test_teams

create-section-homepages: # Create the section homepages
	$(wagtail) python manage.py create_section_homepages

data-countries: # Import the countries data
	$(wagtail) python manage.py loaddata countries.json

ingest-uk-staff-locations: # Create the list of the department's offices
	$(wagtail) python manage.py ingest_uk_staff_locations

local-test-data: # Add all test data for local development
	make data-countries
	make menus
	make create-section-homepages
	make wagtail-groups
	make pf-groups
	make pf-test-teams
	make ingest-uk-staff-locations
	make index

serve-docs: # Serve mkdocs on port 8002
	poetry run mkdocs serve -a localhost:8002
