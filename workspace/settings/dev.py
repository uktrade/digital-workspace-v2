# pylint: disable=unused-wildcard-import, wildcard-import
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '^yz=fa@$1in-6)+@(^yuwfogc=52x*r95o06rvmgy!dre83wv4'

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


try:
    # pylint: disable=wildcard-import
    from .local import *
except ImportError:
    pass
