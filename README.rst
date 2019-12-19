=================
Digital Workspace
=================

A Wagtail_-based intranet for the Department for International Trade.

.. _Wagtail: https://www.wagtail.io

Setup
-----

::

    cp .env.example .env               # ... and set variables as appropriate

    pip install -r requirements.txt
    yarn install

    python3 manage.py migrate
    python3 manage.py createsuperuser
    python3 manage.py runserver

You can now access Digital Workspace on `localhost:8000 <http://localhost:8000>`_
and the admin interface on `localhost:8000/admin <http://localhost:8000/admin>`_.

Assets
------

Assets are handled via Webpack and ``django-webpack-loader``. A number of make
tasks are provided for convenience:

- ``make assets_compile_watch`` watches the asset folder and recompiles on
  changes (useful for development)
- ``make assets_compile`` compiles assets once (useful for deployment)
- ``make assets_clean`` cleans the compiled asset folder (``assets/webpack_bundles``)
