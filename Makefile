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
	docker-compose run wagtail python manage.py migrate
	echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password')" | docker-compose run wagtail python manage.py shell

first-use:
	docker-compose down
	docker-compose run wagtail python manage.py migrate
	docker-compose run wagtail python manage.py fixtree
	docker-compose run wagtail python manage.py create_section_homepages
	echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password')" | docker-compose run wagtail python manage.py shell
	docker-compose run wagtail python manage.py create_menus
	docker-compose up

import:
	docker-compose down
	docker-compose run wagtail python manage.py migrate
	docker-compose run wagtail python manage.py fixtree
	echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password')" | docker-compose run wagtail python manage.py shell
	docker-compose run wagtail python manage.py import_wordpress
	docker-compose run wagtail python manage.py create_menus
	docker-compose up

fixtree:
	docker-compose run wagtail python manage.py fixtree

menus:
	docker-compose run wagtail python manage.py create_menus