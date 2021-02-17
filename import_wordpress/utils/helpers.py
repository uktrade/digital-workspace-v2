import logging
from urllib.parse import urlparse


from django.contrib.auth import get_user_model
from wagtail.core.models import Page
from wagtail.images.models import Image as WagtailImage

from content.models import (
    SearchKeywordOrPhrase,
)


logger = logging.getLogger(__name__)


UserModel = get_user_model()


def get_preview_image(attachments, attachment_id):
    try:
        attachment_url = attachments[attachment_id]["attachment_url"]
        parsed = urlparse(attachment_url)

        return WagtailImage.objects.filter(file=parsed.path[1:]).first()
    except Exception:
        logger.error("Exception when calling 'get_preview_image'", exc_info=True)
        return None


def get_slug(slug, counter=1):
    page_with_slug = Page.objects.filter(slug=slug).first()

    if page_with_slug:
        return get_slug(f"{page_with_slug}-{counter}", (counter + 1))

    return slug





def get_keyword_or_phrase(value):
    keyword_or_phrase = SearchKeywordOrPhrase.objects.filter(
        keyword_or_phrase=value,
    ).first()

    if not keyword_or_phrase:
        keyword_or_phrase = SearchKeywordOrPhrase.objects.create(
            keyword_or_phrase=value,
        )

    return keyword_or_phrase
