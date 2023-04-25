from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from content.models import ContentPage, SearchPinPageLookUp


class Command(BaseCommand):
    help = "Clean up unpinned content pages from the search results"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options) -> None:
        is_dry_run = options["dry_run"]

        count = 0
        deleted = 0

        for content_page in ContentPage.objects.filter(pinned_phrases__isnull=True):
            self.stdout.write(str(content_page))

            if not is_dry_run:
                deleted += self._clean_pinned_phrases(content_page)

            count += 1

        self.stdout.write(self.style.SUCCESS(f"Cleaned up {count} pages"))
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} pins"))

    def _clean_pinned_phrases(self, content_page: ContentPage) -> int:
        if content_page.pinned_phrases:
            return 0

        obj = content_page.get_specific()

        count, _ = SearchPinPageLookUp.objects.filter(
            object_id=obj.pk,
            content_type=ContentType.objects.get_for_model(obj),
        ).delete()

        return count
