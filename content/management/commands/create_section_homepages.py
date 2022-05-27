from django.core.management.base import BaseCommand
from import_wordpress.utils.page_hierarchy import create_section_homepages


class Command(BaseCommand):
    help = "Create section homepages"

    def handle(self, *args, **options):
        create_section_homepages()
