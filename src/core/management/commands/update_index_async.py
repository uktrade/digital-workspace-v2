from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Asynchronously update the search index with Wagtail's `update_index`"
        " command"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            help="Force the update of the search index",
            dest="force",
            default=False,
        )

    def handle(self, *args, **options):
        from core.tasks import update_search_index
        from extended_search.management.commands.create_index_mapping_json import (
            get_indexed_mapping_dict,
        )

        force = options["force"]
        perform_update = force

        if not force:
            # Get the current search mapping hash
            sm_hash = cache.get("search_mapping_hash")

            # Get the search mapping dict
            sm_dict = get_indexed_mapping_dict()
            # Get the hash of the current search mapping dict
            new_sm_hash = hash(frozenset(sm_dict.items()))

            # If the hash of the current search mapping dict is different from the
            # hash of the search mapping dict that was stored in the cache, then
            # update the search index.
            if sm_hash != new_sm_hash:
                cache.set("search_mapping_hash", new_sm_hash)
                perform_update = True

        if not perform_update:
            return

        update_search_index.delay()

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully sent the `update_search_index` task to celery"
            )
        )
