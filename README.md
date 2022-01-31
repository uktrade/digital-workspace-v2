# Digital Workspace

A [Wagtail]-based intranet for the Department for International Trade.

## Setup

```bash
cp .env.example .env               # ... and set variables as appropriate

make build
npm install
npm run build

make first-use               # ... use make up after this has run
```

## Run front end in watch mode

```bash
make webpack
```

You can now access:

- Digital Workspace on http://localhost:8000
- Wagtail admin on http://localhost:8000/admin
- Django admin on http://localhost:8000/django-admin

If you need a virtualenv with the packages installed please run `./setup-local.sh`.
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

## Selenium tests

You can write selenium tests using [selenium](https://selenium-python.readthedocs.io/)
and [pytest-selenium](https://pytest-selenium.readthedocs.io/en/latest/).

The tests are ran against the latest version of Chrome using the Remote WebDriver.

To run the tests make sure you have started the `selenium` docker-compose service. This
can be done using the `selenium` docker-compose
[profile](https://docs.docker.com/compose/profiles/), e.g. `docker-compose --profile selenium up`.
Then you can use the make command `make test-selenium` to run the tests.

All selenium based tests must live in `selenium_tests/`. This is necessary because in
order to get multiple selenium tests to work, the default pytest-django database
handling has to be overridden. See the module docstring for `selenium_tests/conftest.py`
for complete details of selenium based tests.

> Note: It is important that any selenium tests are marked appropriately with
> `@pytest.mark.selenium`.

Please make use of html [data](https://developer.mozilla.org/en-US/docs/Learn/HTML/Howto/Use_data_attributes)
attributes to make your tests more resistant to changes.

This project uses the `data-test-XXX` naming convention for html data attributes which
are there to support tests.

## Coverage

We use [coverage.py](https://coverage.readthedocs.io) to track our test coverage.

To see a coverage report:

```bash
make coverage

# then open ./htmlcov/index.html in a web browser
# OR on linux
xdg-open ./htmlcov/index.html
```

## Make commands

### upgrade-package

Upgrade a single pip package.

Takes a single required argument `package` which is the name of the package you
want to upgade.

Example: `make upgrade-package package=pillow`

## Assets

Assets are handled via Webpack and `django-webpack-loader`. A number of npm
tasks are provided for development:

- `npm run build` compiles assets once
- `npm run dev` watches the asset folder and recompiles on changes
- `npm run clean` cleans the compiled assets in `assets/webpack_bundles`

### Deployment

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

The DIT's people and team directory. Written as a django application inside of Digital
Workspace.

## Design decisions

- Make extensive use of many-to-many fields for multiple choice reference data, e.g.
  country.

## Integrations

- gov.uk notifications
  - notify users about changes made to their profile
- zendesk (via email)
  - left DIT
- mailchimp
  - export subscriber list

## APIs

- data workspace
  - api for people data

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
