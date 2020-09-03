from django.db import models
from content.models import ContentPage

from wagtail.admin.edit_handlers import (
    InlinePanel,
)

from working_at_dit.models import PageWithTopics


class ToolsHome(ContentPage):
    is_creatable = False

    subpage_types = ["tools.Tool"]


class Tool(PageWithTopics):
    is_creatable = True

    redirect_url = models.URLField(null=True, blank=True)

    parent_page_types = ['tools.ToolsHome']
    subpage_types = []  # Should not be able to create children
