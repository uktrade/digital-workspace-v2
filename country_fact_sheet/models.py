import logging

from bs4 import BeautifulSoup
from django import forms
from django.contrib.auth import get_user_model
from django.db import models
from wagtail.admin.edit_handlers import ObjectList, TabbedInterface
from wagtail.admin.forms import WagtailAdminPageForm

from content.models import BasePage, ContentPage
from country_fact_sheet.tasks import process_fact_sheets


UserModel = get_user_model()


logger = logging.getLogger(__name__)


class CountryFactSheetUpload(models.Model):
    UNPROCESSED = "unprocessed"
    PROCESSING = "processing"
    PROCESSED = "processed"
    PROCESSED_WITH_ERROR = "processed_error"
    ANTIVIRUS = "antivirus"
    PROCESSED_WITH_VIRUS = "Found virus"

    STATUS_CHOICES = [
        (UNPROCESSED, "Unprocessed"),
        (ANTIVIRUS, "Checking for viruses"),
        (PROCESSED_WITH_ERROR, "Processed. Page not created, error(s) found."),
        (PROCESSED_WITH_VIRUS, "Processed. Found virus."),
        (PROCESSING, "Processing"),
        (PROCESSED, "Processed and page created"),
    ]

    uploaded_on = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="users"
    )
    country_name = models.CharField(max_length=255)
    s3_document_file = models.FileField(
        max_length=1000,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        default=UNPROCESSED,
    )
    user_error_message = models.TextField(
        null=True,
        blank=True,
    )
    error_message = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )


class CountryFactSheet(BasePage):
    subpage_types = []  # Should not be able to create children
    is_creatable = False

    fact_sheet_content = models.TextField(
        blank=True,
        null=True,
    )

    fact_sheet_content_no_html = models.TextField(
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        self.fact_sheet_content_no_html = BeautifulSoup(
            str(self.fact_sheet_content), "html.parser"
        ).text

        return super().save(*args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["fact_sheet_content"] = self.fact_sheet_content

        return context


class CountryFactSheetHomeForm(WagtailAdminPageForm):
    country_fact_sheets = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data

    def save(self, commit=True):
        page = super().save(commit=False)

        country_fact_sheets = self.cleaned_data["country_fact_sheets"]

        if country_fact_sheets:
            files = self.files.getlist("country_fact_sheets")
            for file in files:
                logger.info(f"Processing '{file.name}' country file")
                # When using a model form, you must use the
                # name attribute of the file rather than
                # passing the request file var directly as this is the
                # required when using the chunk uploader project
                CountryFactSheetUpload.objects.create(
                    s3_document_file=file.name,
                    uploaded_by=self.initial["user"],
                )
            process_fact_sheets.delay()

        if commit:
            page.save()
        return page


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
    subpage_types = [
        "country_fact_sheet.CountryFactSheet",
    ]

    edit_handler = CustomTabbedInterface(
        [
            ObjectList(ContentPage.content_panels, heading="Content"),
            ObjectList(ContentPage.promote_panels, heading="Promote"),
            ObjectList(
                ContentPage.settings_panels, heading="Settings", classname="settings"
            ),
        ]
    )

    def form_valid(self, form, *args, **kwargs):
        return super().form_valid(form, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # TODO - add listing of country fact sheets
        return context

    def get_form_class(self):
        return super().get_form_class()

    def on_request_bound(self):
        return super().on_request_bound()

    base_form_class = CountryFactSheetHomeForm
