from django.db import models
from django.shortcuts import redirect
from content.models import ContentPage

from wagtail.admin.edit_handlers import (
    FieldPanel,
)

from working_at_dit.models import PageWithTopics


class Tool(PageWithTopics):
    is_creatable = True

    redirect_url = models.URLField(null=True, blank=True)

    parent_page_types = ['tools.ToolsHome']
    subpage_types = []  # Should not be able to create children

    content_panels = PageWithTopics.content_panels + [
        FieldPanel('redirect_url'),
    ]

    def serve(self, request):
        return redirect(self.redirect_url)


class ToolsHome(ContentPage):
    is_creatable = False

    subpage_types = ["tools.Tool"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        children = Tool.objects.all().order_by("title")

        context["children"] = children

        return context
