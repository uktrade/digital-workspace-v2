import os
from pathlib import Path

import environ


# Set directories to be used across settings
BASE_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT_DIR = BASE_DIR.parent

# Read environment variables using `django-environ`, use `.env` if it exists
env = environ.Env()
env_file = os.path.join(PROJECT_ROOT_DIR, ".env")
if os.path.exists(env_file):
    env.read_env(env_file)

from .base import *  # noqa

APP_ENV = "build"

SEARCH_ENABLE_QUERY_CACHE = False  # Don't access Redis at build time
