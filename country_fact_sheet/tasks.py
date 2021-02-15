import io
import logging
from datetime import datetime

import boto3
import mammoth
from bs4 import BeautifulSoup
from celery import shared_task
from django.conf import settings
from django.template.defaultfilters import slugify
from wagtail.core.models import Page


logger = logging.getLogger(__name__)


def get_country_name_from_file_name(file_name):
    parts = file_name.split("_")
    return parts[0].capitalize()


def process_html(html):
    soup = BeautifulSoup(html)
    for p in soup.findAll("p"):
        p["class"] = "govuk-body"

    for h1 in soup.findAll("h1"):
        h1["class"] = "govuk-heading-l"

    for h2 in soup.findAll("h2"):
        h2["class"] = "govuk-heading-m"

    for h3 in soup.findAll("h3"):
        h3["class"] = "govuk-heading-m"

    for h4 in soup.findAll("h4"):
        h4["class"] = "govuk-heading-m"

    for h5 in soup.findAll("h5"):
        h5["class"] = "govuk-heading-m"

    for h6 in soup.findAll("h6"):
        h6["class"] = "govuk-body-s"

    for ul in soup.findAll("ul"):
        ul["class"] = "govuk-list"

    for ul in soup.findAll("li"):
        ul["class"] = "govuk-link"

    soup.body.unwrap()
    return str(soup)


@shared_task
def process_fact_sheets():
    from country_fact_sheet.models import (
        CountryFactSheetUpload,
        CountryFactSheet,
    )

    latest_unprocessed = CountryFactSheetUpload.objects.filter(
        status=CountryFactSheetUpload.UNPROCESSED,
    ).all()

    if latest_unprocessed.count() == 0:
        return

    logger.info("Processing uploaded files")

    for file in latest_unprocessed:
        try:
            logger.info(
                f"Processing fact sheet file {file.s3_document_file.name}",
            )

            file.status = CountryFactSheetUpload.PROCESSING
            file.save()

            country_name = get_country_name_from_file_name(
                file.s3_document_file.name,
            )

            s3 = boto3.resource("s3")
            obj = s3.Object(
                settings.AWS_STORAGE_BUCKET_NAME,
                file.s3_document_file.name,
            )
            docx_file = io.BytesIO(obj.get()["Body"].read())

            result = mammoth.convert_to_html(docx_file)
            # TODO - log messages somewhere if relevant
            # messages = result.messages  # Any messages, such as warnings during conversion

            fact_sheet_html = process_html(result.value)

            slug = slugify(f"fact-sheet-{country_name}")

            fact_sheet_page = CountryFactSheet.objects.filter(slug=slug).first()

            if not fact_sheet_page:
                country_fact_sheet_home = Page.objects.filter(
                    slug="country-fact-sheets",
                ).first()

                fact_sheet = CountryFactSheet(
                    first_published_at=datetime.now(),
                    last_published_at=datetime.now(),
                    title=country_name,
                    slug=slug,
                    live=True,
                    fact_sheet_content=fact_sheet_html,
                    depth=3,
                )

                country_fact_sheet_home.add_child(instance=fact_sheet)
                country_fact_sheet_home.save()
            else:
                fact_sheet_page.title = (country_name,)
                fact_sheet_page.fact_sheet_content = fact_sheet_html
                fact_sheet_page.save()

            logger.info("Completed processing file")
            file.status = CountryFactSheetUpload.PROCESSED
            file.save()
        except Exception as ex:
            file.error_message = f"Error processing file, exception: '{ex}'"
            file.user_error_message = (
                "Could not process file, please contact Live Services for help"
            )
            file.status = CountryFactSheetUpload.PROCESSED_WITH_ERROR
            file.save()
