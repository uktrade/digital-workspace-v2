import os

from django.conf import settings
from django.core.management.base import BaseCommand

from import_wordpress.parser.main import parse_xml_file


class Command(BaseCommand):
    help = "Import Wordpress content"

    def handle(self, *args, **options):
        # Parse Wordpress XML and create content
        xml_file = os.path.join(settings.BASE_DIR, "wordpress.xml")
        parse_xml_file(xml_file)
