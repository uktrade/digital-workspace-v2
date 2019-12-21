"""Customisation of Wagtail's admin interface

c.f. https://docs.wagtail.io/en/stable/reference/hooks.html"""

import webpack_loader.utils as webpack_loader_utils

from wagtail.core import hooks

@hooks.register("insert_global_admin_css", order=100)
def global_admin_css():
    """Inject custom CSS from webpack_loader into admin UI"""
    return webpack_loader_utils.get_as_tags('wagtail_admin', 'css')[0]
