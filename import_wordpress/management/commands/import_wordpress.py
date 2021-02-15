from django.core.management.base import BaseCommand

from import_wordpress.parser.main import parse_xml_file


class Command(BaseCommand):
    help = "Import Wordpress content"

    def handle(self, *args, **options):
        # Parse Wordpress XML and create content
        parse_xml_file()
