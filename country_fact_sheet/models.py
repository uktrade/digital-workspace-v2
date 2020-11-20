import logging
import datetime
from bs4 import BeautifulSoup
import mammoth

from django.template.defaultfilters import slugify
from django.contrib.auth import get_user_model
from django.db import models
from django import forms
from django.core.exceptions import ValidationError

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.snippets.models import register_snippet
from content.models import ContentPage


UserModel = get_user_model()


logger = logging.getLogger(__name__)


def get_country_name_from_file_name(file_name):
    # TODO implement
    return "NOT IMPLEMENTED"


class CountryFactSheetUpload(models.Model):
    uploaded_on = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="users"
    )
    country_name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)


class CountryFactSheet(ContentPage):
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
        fact_sheet_string = str(self.fact_sheet)

        self.body_no_html = BeautifulSoup(
            fact_sheet_string,
            "html.parser"
        ).text

        return super().save(*args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        return context


class CountryFactSheetHome(ContentPage):
    subpage_types = ["country_factsheet.CountryFactSheet", ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        return context


class CountryFactSheetHomeForm(WagtailAdminPageForm):
    country_fact_sheets = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={'multiple': True}
        )
    )

    # def clean(self):
    #     cleaned_data = super().clean()
    #
    #     return cleaned_data

    def save(self, commit=True):
        page = super().save(commit=False)

        country_fact_sheets = self.cleaned_data['country_fact_sheets']

        if country_fact_sheets:
            files = country_fact_sheets
            for file in files:
                # TODO - virus scan files
                # TODO - put into celery worker process
                try:
                    logger.info(f"Processing fact sheet file {file.name}")
                    country_name = get_country_name_from_file_name(file.name),

                    with open(file, "rb") as docx_file:
                        result = mammoth.convert_to_html(docx_file)
                        html = result.value  # The generated HTML
                        fact_sheet_page = CountryFactSheet.objects.filter(
                            slug=slugify(file.name)
                        ).first()

                        if not fact_sheet_page:
                            CountryFactSheet.objects.create(
                                title=country_name,
                                slug=slugify(file.name),
                                live=True,
                                first_published_at=datetime.now(),
                                fact_sheet_content=html,
                            )

                        CountryFactSheetUpload.objects.create(
                            uploaded_by=self.request.user,
                            country_name=country_name,
                            file_name=file.name,
                        )

                        # TODO - log messages somewhere if relevant
                        #messages = result.messages  # Any messages, such as warnings during conversion
                except Exception:
                    raise ValidationError(
                        "There was a problem processing your files"
                        "TODO - add further explanation" # TODO
                    )
        if commit:
            page.save()
        return page
