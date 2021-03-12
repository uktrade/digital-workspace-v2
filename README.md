# Digital Workspace

A [Wagtail]-based intranet for the Department for International Trade.

---

## Setup

```bash
cp .env.example .env               # ... and set variables as appropriate

make build
npm install
npm run build

make migrate
make superuser
make up
```

You can now access Digital Workspace on [localhost:8000](http://localhost:8000>)
and the admin interface on [localhost:8000/admin](http://localhost:8000/admin).

If you need a virtualenv with the packages installed please run `./setup-local.sh`.
This is useful if you are using [vscode](https://code.visualstudio.com/) with the
[python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python).

---

## Tests

You can write tests using [pytest](https://docs.pytest.org/en/stable/) and [pytest-django](https://pytest-django.readthedocs.io/en/latest/).

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

---

# Domains

## Dev
workspace.dev.uktrade.digital
static.workspace.dev.uktrade.digital

## Staging
workspace.staging.uktrade.digital
static.workspace.staging.uktrade.digital

# Prod
workspace.trade.gov.uk
static.workspace.trade.gov.uk

[Wagtail]: https://www.wagtail.io

## Notable design decisions
We had to artificially increase the length of the varchar in the following tables so they would work with longer S3 keys:

 * wagtailimages
 * wagtailmedia
 * wagtaildocs

The migration 0010_increase_wagtail_file_field_length_01022021_1252 makes this change

## Notes in import
When importing we will need to copy the content of the current buckets to their new locations (or possibly leave them where they are and update references to them).


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

## Migration process (assumes access to old system is maintained for reference)
Run migrations (5 mins)
Set length of 
Run management command to create Wagtail records for files within S3 bucket (4 hrs)
Run import logic (relies on asset records being in app DB) (1 hr)
Create manual items - quick links, What's Popular, How to list

Redirects to create:

/about-us/networks-at-dit/ -> /networks

# SVG icon license info
https://www.svgrepo.com/page/licensing