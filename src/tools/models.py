from django.db import models
from django.shortcuts import redirect
from wagtail.admin.panels import FieldPanel

from content.models import ContentPage
from working_at_dit.models import PageWithTopics


class Tool(PageWithTopics):
    is_creatable = True

    redirect_url = models.CharField(
        null=True,
        blank=True,
        max_length=2048,
    )

    parent_page_types = ["tools.ToolsHome"]
    subpage_types = []  # Should not be able to create children

    content_panels = PageWithTopics.content_panels + [
        FieldPanel("redirect_url"),
    ]

    def serve(self, request):
        return redirect(self.redirect_url)


class ToolsHome(ContentPage):
    is_creatable = False

    subpage_types = ["tools.Tool"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["children"] = Tool.objects.live().public().order_by("title")

        return context
