# dev_tools

## Installation

Add `dev_tools` to your `INSTALLED_APPS` setting.

```python
INSTALLED_APPS = [
    ...
    "dev_tools"
]
```

Add `dev_tools.context_processors.dev_tools` to your `TEMPLATES` setting.

```python
TEMPLATES = [
    ...
    {
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "dev_tools.context_processors.dev_tools",
            ],
        },
    },
]
```

Add `dev_tools.middleware.DevToolsLoginRequiredMiddleware` to your `MIDDLEWARE` setting.

```python
# You should only add this middleware in dev environments where you have also set `DEV_TOOLS_ENABLED=True`.
MIDDLEWARE = [
    ...
    "dev_tools.middleware.DevToolsLoginRequiredMiddleware",
]
```

Add `dev_tools.urls` to your `urlpatterns`.

```python
urlpatterns = [
    ...
    path("dev-tools/", include("dev_tools.urls")),
]
```

Add the following settings.

```python
# You should disable this in production!
DEV_TOOLS_ENABLED = True
DEV_TOOLS_LOGIN_URL = None
DEV_TOOLS_DEFAULT_USER = None

# Optional - if you want to be automatically logged in as a default user.

# Use the dev_tools login view.
DEV_TOOLS_LOGIN_URL = "dev_tools:login"
# Primary key of the default user.
DEV_TOOLS_DEFAULT_USER = 1
```

Add `dev_tools_dialog` to your base template:

```html
<!-- Load dev_tools -->
{% load dev_tools %}
<!-- Add the dialog -->
{% dev_tools_dialog %}
<!-- Add a way to open the dialog -->
<button onclick="openDevToolsDialog()">Dev tools</button>
```
