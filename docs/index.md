---
hide:
  - navigation
---

# About

Digital Workspace is the intranet for the Department for Business and Trade (DBT) built using [Wagtail](https://www.wagtail.io) and [Django](https://www.djangoproject.com/).

## Setup

```bash
cp .env.example .env         # ... and set variables as appropriate *

make setup
```

**You will need SSO auth details (`AUTHBROKER_*` in your `.env` file) to allow the project to run, but there are a lot of other details that would help make the experience better; ask another dev for their .env so that you can get a head start.**

## Run front end in watch mode

```bash
make webpack
```

If you're on a local (non-production!) environment you may want to ensure that `DEV_TOOLS_ENABLED` is set to `True` to avoid integrating with the SSO service. This is a workaround to allow developers to impersonate different users and should be used with caution.

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

- [Project playbook](https://readme.trade.gov.uk/docs/playbooks/workspace.html)
- [Wagtail](https://www.wagtail.io)
- [Django](https://www.djangoproject.com/)

## Setup DebugPy

Add environment variable in your .env file

```bash
DEBUGPY_ENABLED=True
```

Create launch.json file inside .vscode directory

```bash
    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Remote Attach (DebugPy)",
                "type": "debugpy",
                "request": "attach",
                "connect": {
                    "host": "localhost",
                    "port": 5678
                },
                "pathMappings": [
                    {
                        "localRoot": "${workspaceFolder}",
                        "remoteRoot": "/app/"
                    }
                ],
                "justMyCode": true
            }
        ]
    }
```

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

I am creating a management command to do the above. - Ross Miller

## SVG icon license info

https://www.svgrepo.com/page/licensing
