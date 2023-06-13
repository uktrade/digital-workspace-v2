from django import forms
from django.db import models
from django.shortcuts import redirect
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel

from content.models import ContentPage
from working_at_dit.models import PageWithTopics

class IrapDataAbstract(models.Model):
    product_irap_reference_number = models.IntegerField(primary_key=True)
    product_name = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
    )
    functionality = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
    )
    latest_accreditation_status = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

class IrapData(IrapDataAbstract):
    pass


class Tool(PageWithTopics, IrapDataAbstract):
    is_creatable = True
    product_irap_reference_number = models.IntegerField(blank=True, null=True)

    redirect_url = models.CharField(
        null=True,
        blank=True,
        max_length=2048,
    )
    long_description = models.CharField(
        null=True,
        blank=True,
        max_length=2048,
    )

    # using the correct widget for your field type and desired effect
    readonly_widget = forms.TextInput(
        attrs = {
            'disabled': 'true'
        }
    )

    parent_page_types = ["tools.ToolsHome"]
    subpage_types = []  # Should not be able to create children

    content_panels = PageWithTopics.content_panels + [
        FieldPanel("redirect_url"),
        HelpPanel("long_description"),
        MultiFieldPanel(
            [
                FieldPanel("product_irap_reference_number", widget=readonly_widget),
                FieldPanel("product_name", widget=readonly_widget),
                FieldPanel("functionality", widget=readonly_widget),
            ],
            heading="IRAP Fields (Read Only)",
            classname="collapsed",
        )

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
