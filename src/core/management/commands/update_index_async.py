from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Asynchronously update the search index with Wagtail's `update_index`"
        " command"
    )

    def handle(self, *args, **options):
        from core.tasks import update_search_index

        update_search_index.delay()

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully sent the `update_search_index` task to celery"
            )
        )
