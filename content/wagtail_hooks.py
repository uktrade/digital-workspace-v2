"""Customisation of Wagtail's admin interface

c.f. https://docs.wagtail.io/en/stable/reference/hooks.html"""

import webpack_loader.utils as webpack_loader_utils

from wagtail.core import hooks
from wagtail.documents.rich_text import DocumentLinkHandler

from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import filesizeformat
from django.utils.html import escape

@hooks.register("insert_global_admin_css", order=100)
def global_admin_css():
    """Inject custom CSS from webpack_loader into admin UI"""
    return webpack_loader_utils.get_as_tags('wagtail_admin', 'css')[0]

class DocumentWithTypeAndSizeLinkHandler(DocumentLinkHandler):
    """Override DocumentLinkHandler to provide size and type info

    This is a nasty hack to allow us to automatically append the type and size
    of a Wagtail document to the link in the frontend. Because Wagtail only
    replaces the start tag in a link handler and we cannot modify the link
    text, our only option is to put this meta info just after the start tag and
    move it to the end using CSS.
    """
    @classmethod
    def expand_db_attributes(cls, attrs):
        try:
            doc = cls.get_instance(attrs)
            url = escape(doc.url)
            size = filesizeformat(doc.file_size)
            ext = doc.file_extension.upper()

            return (f'<a class="document-link" href="{url}">'
                    f'<span class="document-link-meta">({ext}, {size})</span> ')
        except (ObjectDoesNotExist, KeyError):
            return "<a>"

@hooks.register('register_rich_text_features', order=100)
def register_external_link(features):
    features.register_link_type(DocumentWithTypeAndSizeLinkHandler)
