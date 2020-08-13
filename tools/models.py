from wagtail.core.models import Page

from working_at_dit.models import PageWithTopics


class ToolsHome(Page):
    is_creatable = False

    subpage_types = ["tools.Tool"]


class Tool(PageWithTopics):
    is_creatable = True

    parent_page_types = ['tools.ToolsHome']
    subpage_types = []  # Should not be able to create children
