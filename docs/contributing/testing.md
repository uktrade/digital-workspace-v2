# Testing


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

> Note: if you're running e2e tests many times in a session and don't want to destroy and recreate the DB each time (to make the run faster), set the `TESTS_KEEP_DB` environment variable to a truthy value (most easily by modifying .env.ci)

### E2E codegen tests

When writing playwright tests it might be useful to use the `make e2e-codegen` tool to help generate code.
If you need to log into the admin side of the site then you can add the following to `config/urls.py`:

```python
# Test admin login
def login_as_admin(request):
    from django.contrib.auth import login

    from user.models import User

    user = User.objects.filter(is_superuser=True).first()
    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend",
    )
    return RedirectView.as_view(url="/")(request)

urlpatterns = [
    path("login-as-admin/", login_as_admin),
] + urlpatterns
```

Then when you are browsing the site you can go to `/login-as-admin/` to which will find a superuser and log you in as them.


## Coverage

We use [coverage.py](https://coverage.readthedocs.io) to track our test coverage.

To see a coverage report:

```bash
make coverage

# then open ./htmlcov/index.html in a web browser
# OR on linux
xdg-open ./htmlcov/index.html
```

