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
	docker-compose run --rm wagtail python manage.py elevate_sso_user_permissions --email=$(email)

collectstatic:
	docker-compose run --rm wagtail python manage.py collectstatic

findstatic:
	docker-compose run --rm wagtail python manage.py findstatic $(app)

bash:
	docker-compose run --rm wagtail bash

all-requirements:
	docker-compose run --rm --no-deps wagtail pip-compile --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm --no-deps wagtail pip-compile --output-file requirements/dev.txt requirements.in/dev.in

upgrade-package:
	docker-compose run --rm --no-deps wagtail pip-compile --upgrade-package $(package) --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm --no-deps wagtail pip-compile --upgrade-package $(package) --output-file requirements/dev.txt requirements.in/dev.in

upgrade-all-packages:
	docker-compose run --rm --no-deps wagtail pip-compile --upgrade --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm --no-deps wagtail pip-compile --upgrade --output-file requirements/dev.txt requirements.in/dev.in

superuser:
	docker-compose run --rm wagtail python manage.py shell --command="from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', email='admin', password='password', first_name='admin', last_name='test')"

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

first-use:
	docker-compose down
	make migrate
	make menus
	make create_section_homepages
	make groups
	make superuser
	docker-compose up
