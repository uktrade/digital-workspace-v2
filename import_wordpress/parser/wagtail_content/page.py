import abc
import json
import logging
from abc import ABC
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from wagtail.core.models import Page
from wagtail.documents.models import Document as WagtailDocument
from wagtail.images.models import Image as WagtailImage

from import_wordpress.parser.block_content import (
    parse_into_blocks,
)
from working_at_dit.models import PageTopic, Topic


UserModel = get_user_model()

logger = logging.getLogger(__name__)


def get_page_path(full_path):
    parts = full_path.split("/")
    return f'{"/".join(parts[-2])}/'


ARCHIVE_STR_LIST = (
    "[archived]",
    "[ARCHIVED]",
    "[ARCHIVE]",
    "Archive - ",
    "ARCHIVED",
)


class WPPage(ABC):
    def __init__(self, page_content, path=None, attachments=[]):  # noqa B006
        logger.info(f"Creating page with path: {path}")
        self.path = path
        self.page_content = page_content
        self.attachments = attachments
        self.wagtail_page = None

        if not self.live:
            logger.warning("Page is not live")

    @property
    def archived(self):
        for archive_str in ARCHIVE_STR_LIST:
            if self.page_content["title"] in archive_str:
                return False

        return True

    @property
    def live(self):
        return self.page_content["status"] == "publish"

    @property
    def title(self):
        title = self.page_content["title"]
        if not title or title.strip() == "":
            title = "NO TITLE"

        return title

    @property
    def pinned(self):
        pinned_str = ""
        for pinned in self.page_content["search_pinned"]:
            pinned_str = pinned_str + f"{pinned}, "

        return pinned_str

    @property
    def excluded(self):
        exclude_str = ""
        for excluded in self.page_content["search_excluded"]:
            exclude_str = exclude_str + f"{excluded}, "

        return exclude_str

    @property
    def author(self):
        domains = [
            "trade.gov.uk",
            "digital.trade.gov.uk",
            "trade.gsi.gov.uk",
        ]

        author = None

        # Exceptions to general pattern
        if self.page_content["creator"] == settings.AUTHOR_TO_BE_SUBSTITUTED:
            self.page_content["creator"] = settings.AUTHOR_SUBSTITUTED

        for domain in domains:
            author_email = f'{self.page_content["creator"].lower()}@{domain}'
            author = UserModel.objects.filter(email=author_email).first()

            if author:
                break

        if not author:
            logger.warning(f"Could not find author: '{self.page_content['creator']}'")
            author = UserModel.objects.filter(
                email="connect@digital.trade.gov.uk"
            ).first()

        return author

    def set_topics(self):
        # Set relationship with Topic pages
        if "topics" in self.page_content:
            for wp_topic in self.page_content["topics"]:
                topic = Topic.objects.filter(title=wp_topic["name"]).first()

                if not topic:  #  Some topics have been archived
                    logger.warning(
                        f'SKIPPED TOPIC: "{wp_topic["name"]}" for page "{self.wagtail_page}"'
                    )
                    continue

                PageTopic.objects.get_or_create(
                    topic=topic,
                    page=self.wagtail_page,
                )
                self.wagtail_page.save()

    def assign_documents(self):
        for document_file_post_id in self.page_content["document_files"]:
            for _key, value in self.attachments.items():
                if value["post_id"] == document_file_post_id:
                    title = value["content"]

                    attachment_url = value["attachment_url"]
                    parsed = urlparse(attachment_url)
                    s3_path = parsed.path[1:]

                    document = WagtailDocument.objects.filter(
                        file=s3_path,
                    ).first()

                    if not document:
                        logger.warning(f"COULD NOT FIND DOCUMENT: '{s3_path}'")
                    else:
                        if title:
                            document.title = title
                            document.save()

    def get_preview_image(self, attachment_id):
        try:
            attachment_url = self.attachments[attachment_id]["attachment_url"]
            parsed = urlparse(attachment_url)

            return WagtailImage.objects.filter(file=parsed.path[1:]).first()
        except Exception:
            logger.error("Exception when calling 'get_preview_image'", exc_info=True)
            return None

    def get_slug(self, slug, counter=1):
        page_with_slug = Page.objects.filter(slug=slug).first()

        if page_with_slug:
            return self.get_slug(f"{page_with_slug}-{counter}", (counter + 1))

        return slug

    @abc.abstractmethod
    def create(self):
        """Child classes must implement this and populate self.wagtail_page"""
        return

    @abc.abstractmethod
    def get_parent(self):
        """Child classes can implement this if they need to carry out post create processes"""
        return

    def post_create(self):
        parent = self.get_parent()

        if "excerpt" in self.page_content and self.page_content["excerpt"]:
            self.wagtail_page.excerpt = self.page_content["excerpt"]

        if "redirect_url" in self.page_content:
            self.wagtail_page.redirect_url = self.page_content["redirect_url"]

        parent.add_child(instance=self.wagtail_page)
        parent.save()

        if self.page_content["content"]:
            block_content = parse_into_blocks(
                self.page_content["content"],
                self.attachments,
            )

            self.wagtail_page.body = json.dumps(block_content)

        self.set_topics()
        self.assign_documents()

        self.wagtail_page.save()

        if self.live:
            revision = self.wagtail_page.save_revision(
                user=self.author,
                submitted_for_moderation=False,
            )
            revision.publish()
            self.wagtail_page.save()

        return self.wagtail_page


class SectionHomepage(WPPage):
    def __init__(
        self, page_content, content_class, path=None, attachments=[]  # noqa B006
    ):
        super().__init__(page_content, path, attachments)
        self.content_class = content_class

    def get_parent(self):
        raise NotImplementedError()

    def create(self):
        self.wagtail_page = self.content_class.objects.filter(
            slug=slugify(self.path)
        ).first()

        self.wagtail_page.first_published_at = self.page_content["pub_date"]
        self.wagtail_page.last_published_at = self.page_content["post_date"]
        self.wagtail_page.title = self.title
        self.wagtail_page.legacy_guid = self.page_content["guid"]
        self.wagtail_page.legacy_path = self.path
        self.wagtail_page.legacy_content = self.page_content["content"]
        self.wagtail_page.live = self.live
        self.wagtail_page.save()

        block_content = parse_into_blocks(
            self.page_content["content"],
            self.attachments,
        )

        self.wagtail_page.body = json.dumps(block_content)
        self.set_topics()

        revision = self.wagtail_page.save_revision(
            user=self.author,
            submitted_for_moderation=False,
        )
        revision.publish()
        self.wagtail_page.save()

        return self.wagtail_page


class StandardPage(WPPage):
    def __init__(
        self,
        page_content,
        content_class,
        parent,
        path=None,
        attachments=[],  # noqa B006
    ):
        super().__init__(page_content, path, attachments)
        self.content_class = content_class
        self.parent_object = parent

    def get_parent(self):
        return self.parent_object

    def create(self):
        self.wagtail_page = self.content_class(
            first_published_at=self.page_content["pub_date"],
            last_published_at=self.page_content["post_date"],
            title=self.title,
            slug=slugify(get_page_path(self.path)),
            legacy_path=self.path,
            legacy_guid=self.page_content["guid"],
            legacy_content=self.page_content["content"],
            live=self.live,
            pinned_phrases=self.pinned,
            excluded_phrases=self.excluded,
        )
        self.post_create()

        return self.wagtail_page
