from import_wordpress.parser.main import parse_xml_file

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import Wordpress content"

    def handle(self, *args, **options):
        # Parse Wordpress XML and create content
        parse_xml_file()
