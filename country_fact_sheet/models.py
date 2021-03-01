import logging

from django.contrib.auth import get_user_model
from django.db import models
from wagtail.admin.edit_handlers import (
    FieldPanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.documents.models import Document

from content.models import ContentPage


UserModel = get_user_model()


logger = logging.getLogger(__name__)


class CustomTabbedInterface(TabbedInterface):
    def get_form_class(self):
        form_class = super().get_form_class()
        request = self.request
        if request:
            # check request is available to ensure this instance has been bound to it
            user = self.request.user

            def initiate_class(*args, **kwargs):
                # instead of returning the class, return a function that returns the instantiated class
                # here we can inject a kwarg `initial` into the generated form
                # important: this gets called for edit view also and initial will override the instance data
                # kwarg['instance'] will be the `Page` instance and can be inspected as needed
                kwargs["initial"] = {"user": user}

                return form_class(*args, **kwargs)

            return initiate_class

        return form_class


class CountryFactSheetHome(ContentPage):
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

    hmtc_region_factsheets_heading = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="HMTC region factsheets heading",
    )
    group_factsheets_heading = models.CharField(
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

    edit_handler = CustomTabbedInterface(
        [
            ObjectList(content_panels, heading="Content"),
            ObjectList(ContentPage.promote_panels, heading="Promote"),
            ObjectList(
                ContentPage.settings_panels, heading="Settings", classname="settings"
            ),
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        return super().form_valid(form, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        if context["page"].hmtc_region_factsheets_collection:
            context["hmtc_region_factsheets"] = Document.objects.filter(
                collection=context["page"].hmtc_region_factsheets_collection
            ).order_by("title")

        if context["page"].group_factsheets_collection:
            context["group_factsheets"] = Document.objects.filter(
                collection=context["page"].group_factsheets_collection
            ).order_by("title")

        return context

    def get_form_class(self):
        return super().get_form_class()

    def on_request_bound(self):
        return super().on_request_bound()
