# Digital Workspace

![AWS Codebuild status](https://codebuild.eu-west-2.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiSWg0Z3RpTEFhL1NBVDJ5a1RuS0ZGZHMra01sQm9xbkYraFRUeTJacmcvRWFGY0VlUUxJVHJJTlRRVk9nbVlPemw2MUE0L2FnSDZQZEc0ZVM3eTNOZnhFPSIsIml2UGFyYW1ldGVyU3BlYyI6Inc4MnlOdmo1eXd2RGNBWkwiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=main)

A [Wagtail]-based intranet for the Department for Business & Trade.

## Setup

```bash
cp .env.example .env         # ... and set variables as appropriate *

make build
npm install
npm run build

make first-use               # ... use make up after this has run
```

\* You will need SSO auth details (`AUTHBROKER_*` in your `.env` file) to allow the project to run, but there are a lot of other details that would help make the experience better; ask another dev for their .env so that you can get a head start.

## Run front end in watch mode

```bash
make webpack
```

You can now access:

- Digital Workspace on http://localhost:8000
- Wagtail admin on http://localhost:8000/admin
- Django admin on http://localhost:8000/django-admin

If you would like a virtualenv with the packages installed then:

- make sure you have [Poetry](https://python-poetry.org/docs/#installation) installed
- run `make local-setup`

This is useful if you are using [vscode](https://code.visualstudio.com/) with the
[python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python).

## Useful commands

```bash
# Start a bash session
make bash
# Create test users
python manage.py create_test_users
# Create user profiles
python manage.py create_user_profiles
# Create test teams
python manage.py create_test_teams
exit # leave the container's bash shell

# Rebuild the search index
make index
```

## Managing Python dependencies

This project uses [Poetry](https://python-poetry.org) for dependency management.

We recommend reading through the [docs](https://python-poetry.org/docs/), in particular
the sections on the [CLI](https://python-poetry.org/docs/cli/) and [Dependency
specification](https://python-poetry.org/docs/dependency-specification/).

Below is an example of how to use Poetry to handle the dependencies in this project.

```bash
# Start a bash session
make bash
# Update all packages (respects the version constraints in pyproject.toml)
poetry update
# Update selected packages (respects the version constraints in pyproject.toml)
poetry update django wagtail
# Update a package to a version outside it's constraints
poetry add django@^4.0.0
# Don't forget to regenerate the requirements.txt file
make requirements
```

## Unit tests

You can write tests using [pytest](https://docs.pytest.org/en/stable/) and
[pytest-django](https://pytest-django.readthedocs.io/en/latest/).

```bash
# Run all tests
make test

# Run selected tests
make test tests=peoplefinder

# Run tests interactively
make bash
pytest

# To recreate the database use the --create-db flag
make test tests="peoplefinder --create-db"
# or interactively
make bash
pytest --create-db
```

The pytest settings can be found in the `pyproject.toml` file.

## End to end tests

End-to-end (e2e) tests only run in CI against the master/main branch, and any branch with
`e2e` in the branch name.

[Playwright](https://playwright.dev/python/) is used as the e2e test runner, using the python variant,
and executed with `pytest-playwright`.

To run the tests make sure you have started the `playwright` docker-compose service. This
can be done using the `playwright` docker-compose
[profile](https://docs.docker.com/compose/profiles/), e.g. `docker-compose --profile playwright up`.
Then you can use the make command `make test-e2e` to run the tests.

Playwright tests live in the `e2e_tests` folder for convenience.

> Note: It is important that any e2e tests are marked appropriately with
> `@pytest.mark.e2e` so they don't run in unit-test runs.

Please make use of html [data](https://developer.mozilla.org/en-US/docs/Learn/HTML/Howto/Use_data_attributes)
attributes to make your tests more resistant to changes.

This project uses the `data-testid="XXX"` naming convention for html data attributes which
are there to support tests.

Playwright also has a [test generator](https://playwright.dev/python/docs/codegen-intro) -
install the dependencies on your host machine and run `make e2e-codegen` to generate test cases
as you browse (using the CI settings).

> Note: if you're running e2e tests many times in a session and don't want to destroy and recreate the DB each time (to make the run faster), set the `TESTS_KEEP_DB` environment variable to a truthy value (most easily by modifying .env.ci)

## Coverage

We use [coverage.py](https://coverage.readthedocs.io) to track our test coverage.

To see a coverage report:

```bash
make coverage

# then open ./htmlcov/index.html in a web browser
# OR on linux
xdg-open ./htmlcov/index.html
```

## Assets

Assets are handled via Webpack and `django-webpack-loader`. A number of npm
tasks are provided for development:

- `npm run build` compiles assets once
- `npm run dev` watches the asset folder and recompiles on changes
- `npm run clean` cleans the compiled assets in `assets/webpack_bundles`

## Deployment

On deployment, assets need to be compiled on CI before `collectstatic` is run.
We achieve this by using both the Python and NodeJS buildpacks, the NodeJS
buildpack will automatically run the npm `heroku-postbuild` step after
`npm install`.

## Further reading

https://readme.trade.gov.uk/docs/playbooks/workspace.html

[wagtail]: https://www.wagtail.io

## Notable design decisions

We had to artificially increase the length of the varchar in the following tables so they would work with longer S3 keys:

- wagtailimages
- wagtailmedia
- wagtaildocs

The migration 0010_increase_wagtail_file_field_length_01022021_1252 makes this change

## S3 - transfer of assets and security

The use of the original project bucket will be maintained. This bucket is
hooked up to the static.workspace.trade.gov.uk asset serving service which
provides SSO authenticated access to the assets within it.

S3Boto3Storage from django storages is used for media storage configuration,
meaning that files are written to S3 on save. django storages has been configured
through the use of the AWS_S3_CUSTOM_DOMAIN setting to use static.workspace.trade.gov.uk
as the domain for serving media assets.

So, when a media file is saved, it is sent to S3 but the page rendered to the URL
for that asset uses the SSO authenticated service at static.workspace.trade.gov.uk

In order to make Wagtail images, document, video record aware of the content of
the bucket we need to iterate through the bucket content and create the relevant records.

I am creating a management command to do the above.

## SVG icon license info

https://www.svgrepo.com/page/licensing

# People Finder

The DIT's people and team directory. Written as a Django application inside of Digital
Workspace.

## Design decisions

- Make extensive use of many-to-many fields for multiple choice reference data, e.g.
  country.

### Soft Delete

When a profile is deleted by an admin, they are marked as inactive. If the user
connected to the profile attempts to access the system, they will be redirected to a
page explaining they have been deactivated. Inactive profiles will only be visible to
admins and can only be reactivated by admins.

To support this feature in the codebase, the `Person` model and the `TeamMember` model
both have an `active` manager which filters for active people. Both models retain
the unfiltered `objects` manager as their default, so that the system can access
inactive profiles for admins to manage. To make things easier, both models' `objects`
manager have an `active()` queryset method to filter for active profiles. This is useful
when you are performing queries across related managers which use the default `objects`
manager.

Here are some examples:

```python
# All users.
Person.objects.all()

# Active users.
Person.active.all()
Person.objects.active()

# All team members.
TeamMember.objects.all()

# Active team members.
TeamMember.active.all()
TeamMember.objects.active()

# All team members through a related team.
team.members.all()

# Active team members through a related team.
team.members.active()
# https://docs.djangoproject.com/en/4.0/topics/db/queries/#using-a-custom-reverse-manager
team.members(manager="active").all()
```

Please take care to make sure any code you write uses the correct manager, or applies
the appropriate filters for your use case.

## Integrations

- GOV.UK Notify
  - Notify users about changes made to their profile
- Zendesk (via email)
  - Creates a ticket when a person is marked as having left the DIT

## APIs

- Data Workspace
  - API for people data

## Audit log

**Please remember to use the audit log service after you have made model instance
changes that you wish to be tracked!**

After evaluating a number of packages, we decided to write our own audit log system. The
main reason for doing this is because no package would track changes to many-to-many
fields without us having to make changes to how the app is written. Therefore, we
decided it was best to keep the implementation of the app simple and write our own audit
log system.

The audit log system we have written does not make use of django signals. This is
because that approach has difficulties handling many-to-many fields. Instead, we have a
simple and explicit approach where you must call the audit log service after you have
made changes for them to be tracked.

For this approach to work you will need to provide a flat, serialized and denormalized
"view" of the model you wish to be tracked. This allows us to avoid the complexity of
tracking many-to-many fields by denormalizing them. This is often achieved using
`ArrayAgg` which provides an array representation of the many-to-many relationship. For
an example of this in action, please take a look at the `PersonAuditLogSerializer` class
in `peoplefinder/services/person.py`.

One downside to this approach is that if you do not call the audit log service after
making a change, for example modifying a model instance in a shell, then the changes
will not be tracked.

For more information, please read through the docstrings and code in
`peoplefinder/services/audit_log.py` and check out an example of how to use the service
from a view in the `ProfileEditView` class in `peoplefinder/views/profile.py`.
