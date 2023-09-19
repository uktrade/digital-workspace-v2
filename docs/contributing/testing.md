# Testing

## Test commands

- `make test`
- `make test-e2e`

## E2E codegen tests

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
