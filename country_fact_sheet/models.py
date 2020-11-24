import logging
from datetime import datetime
from bs4 import BeautifulSoup
import mammoth

from django.template.defaultfilters import slugify
from django.contrib.auth import get_user_model
from django.db import models
from django import forms
from django.core.exceptions import ValidationError

from wagtail.core.models import Page
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.snippets.models import register_snippet
from content.models import BasePage, ContentPage

from wagtail.admin.edit_handlers import (
    FieldPanel,
)


UserModel = get_user_model()


logger = logging.getLogger(__name__)


def get_country_name_from_file_name(file_name):
    parts = file_name.split()
    return parts[0]


def process_html(html):
    soup = BeautifulSoup(html)
    for p in soup.findAll('p'):
        p['class'] = 'govuk-body'

    for h1 in soup.findAll('h1'):
        h1['class'] = 'govuk-heading-l'

    for h2 in soup.findAll('h2'):
        h2['class'] = 'govuk-heading-m'

    for h3 in soup.findAll('h3'):
        h3['class'] = 'govuk-heading-m'

    for h4 in soup.findAll('h4'):
        h4['class'] = 'govuk-heading-m'

    for h5 in soup.findAll('h5'):
        h5['class'] = 'govuk-heading-m'

    for h6 in soup.findAll('h6'):
        h6['class'] = 'govuk-body-s'

    for ul in soup.findAll('ul'):
        ul['class'] = 'govuk-list'

    for ul in soup.findAll('li'):
        ul['class'] = 'govuk-link'

    soup.body.unwrap()
    return str(soup)


# class CountryFactSheetUpload(models.Model):
#     uploaded_on = models.DateTimeField(auto_now_add=True)
#     uploaded_by = models.ForeignKey(
#         get_user_model(),
#         on_delete=models.CASCADE,
#         related_name="users"
#     )
#     country_name = models.CharField(max_length=255)
#     file_name = models.CharField(max_length=255)


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
            str(self.fact_sheet_content),
            "html.parser"
        ).text

        return super().save(*args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["fact_sheet_content"] = self.fact_sheet_content

        return context


class CountryFactSheetHomeForm(WagtailAdminPageForm):
    country_fact_sheets = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={'multiple': True}
        ),
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data

    def save(self, commit=True):
        page = super().save(commit=False)

        country_fact_sheets = self.cleaned_data['country_fact_sheets']

        if country_fact_sheets:
            files = self.files.getlist('country_fact_sheets')
            for file in files:
                # TODO - virus scan files
                # TODO - put into celery worker process
                # try:
                logger.info(f"Processing fact sheet file {file.name}")
                country_name = get_country_name_from_file_name(file.name)

                with file.open() as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    fact_sheet_html = process_html(result.value)

                    fact_sheet_page = CountryFactSheet.objects.filter(
                        slug=slugify(file.name)
                    ).first()

                    if not fact_sheet_page:
                        country_fact_sheet_home = Page.objects.filter(
                            slug="country-fact-sheets",
                        ).first()

                        fact_sheet = CountryFactSheet(
                            first_published_at=datetime.now(),
                            last_published_at=datetime.now(),
                            title=country_name,
                            slug=slugify(file.name),
                            live=True,
                            fact_sheet_content=fact_sheet_html,
                            depth=3,
                        )

                        country_fact_sheet_home.add_child(instance=fact_sheet)
                        country_fact_sheet_home.save()
                    else:
                        fact_sheet_page.fact_sheet_content = fact_sheet_html
                        fact_sheet_page.save()

                    # TODO - log messages somewhere if relevant
                    #messages = result.messages  # Any messages, such as warnings during conversion
                # except Exception as ex:
                #     raise ValidationError(
                #         f"There was a problem processing your files - {ex}"
                #         "TODO - add further explanation" # TODO
                #     )
        if commit:
            page.save()
        return page


class CountryFactSheetHome(ContentPage):
    subpage_types = ["country_fact_sheet.CountryFactSheet", ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        return context

    content_panels = ContentPage.content_panels + [
        FieldPanel('country_fact_sheets'),
    ]

    base_form_class = CountryFactSheetHomeForm
