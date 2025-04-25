import logging

from django.contrib.auth import get_user_model
from django.db import models
from wagtail.admin.panels import MultiFieldPanel
from wagtail.documents.models import Document

from content.models import ContentPage
from core import field_models
from core.panels import FieldPanel


UserModel = get_user_model()


logger = logging.getLogger(__name__)


class CountryFactSheetHome(ContentPage):
    template = "country_fact_sheet/country_fact_sheet_home.html"
    country_factsheets_help_text = (
        "Uploaded PDF documents in the selected collection will be displayed"
        " as a list of country factsheets on the page."
    )

    hmtc_region_factsheets_collection = models.ForeignKey(
        "wagtailcore.Collection",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="HMTC region factsheets collection",
    )
    group_factsheets_collection = models.ForeignKey(
        "wagtailcore.Collection",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Group factsheets collection",
    )

    hmtc_region_factsheets_heading = field_models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="HMTC region factsheets heading",
    )
    group_factsheets_heading = field_models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Group factsheets heading",
    )

    content_panels = ContentPage.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hmtc_region_factsheets_heading"),
                FieldPanel("hmtc_region_factsheets_collection"),
            ],
            heading="HMTC region factsheets",
            help_text=country_factsheets_help_text,
        ),
        MultiFieldPanel(
            [
                FieldPanel("group_factsheets_heading"),
                FieldPanel("group_factsheets_collection"),
            ],
            heading="Group factsheets",
            help_text=country_factsheets_help_text,
        ),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["attribution"] = True

        if context["page"].hmtc_region_factsheets_collection:
            context["hmtc_region_factsheets"] = Document.objects.filter(
                collection=context["page"].hmtc_region_factsheets_collection
            ).order_by("title")

        if context["page"].group_factsheets_collection:
            context["group_factsheets"] = Document.objects.filter(
                collection=context["page"].group_factsheets_collection
            ).order_by("title")

        return context
