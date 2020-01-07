# Digital Workspace

A [Wagtail]-based intranet for the Department for International Trade.

## Setup

```bash
cp .env.example .env               # ... and set variables as appropriate

pip install -r requirements.txt
yarn install

python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

You can now access Digital Workspace on [localhost:8000](http://localhost:8000>)
and the admin interface on [localhost:8000/admin](http://localhost:8000/admin).

## Assets

Assets are handled via Webpack and `django-webpack-loader`. A number of make
tasks are provided for convenience:

- `make assets_compile_watch` watches the asset folder and recompiles on
  changes (useful for development)
- `make assets_compile` compiles assets once (useful for deployment)
- `make assets_clean` cleans the compiled assets in `assets/webpack_bundles`

[Wagtail]: https://www.wagtail.io
