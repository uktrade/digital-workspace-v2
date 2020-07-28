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

lint:
	flake8

clean:
	npm run clean
	find . -name '__pycache__' -exec rm -rf {} +

makemigrations:
	docker-compose run wagtail python manage.py makemigrations

migrations:
	docker-compose run wagtail python manage.py makemigrations

migrate:
	docker-compose run wagtail python manage.py migrate

compilescss:
	docker-compose run wagtail python manage.py compilescss

test:
	docker-compose run wagtail python manage.py test $(test)

shell:
	docker-compose run wagtail python manage.py shell

flake8:
	docker-compose run wagtail flake8

up:
	docker-compose up

down:
	docker-compose down

build:
	docker-compose build

elevate:
	docker-compose run wagtail python manage.py elevate_sso_user_permissions

collectstatic:
	docker-compose run wagtail python manage.py collectstatic

bash:
	docker-compose run wagtail bash

dev-requirements:
	pip-compile --output-file requirements/base.txt requirements.in/base.in
	pip-compile --output-file requirements/dev.txt requirements.in/dev.in

production-requirements:
	pip-compile --output-file requirements/base.txt requirements.in/base.in
	pip-compile --output-file requirements/production.txt requirements.in/production.in

superuser:
	docker-compose run wagtail python manage.py createsuperuser

import:
	docker-compose run wagtail python manage.py migrate
	docker-compose run wagtail python manage.py fixtree
	docker-compose run wagtail python manage.py import_wordpress

fixtree:
	docker-compose run wagtail python manage.py fixtree
