# Digital Workspace

A [Wagtail]-based intranet for the Department for International Trade.

---

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

---

## Assets

Assets are handled via Webpack and `django-webpack-loader`. A number of yarn
tasks are provided for development:

- `yarn build` compiles assets once
- `yarn dev` watches the asset folder and recompiles on changes
- `yarn clean` cleans the compiled assets in `assets/webpack_bundles`

### Deployment

On deployment, assets need to be compiled on CI before `collectstatic` is run.
We achieve this by using both the Python and NodeJS buildpacks, the NodeJS
buildpack will automatically run the yarn `heroku-postbuild` step after
`yarn install`.

---

[Wagtail]: https://www.wagtail.io
