# pylint: disable=unused-wildcard-import, wildcard-import
from .base import *

DEBUG = False

try:
    # pylint: disable=wildcard-import
    from .local import *
except ImportError:
    pass
