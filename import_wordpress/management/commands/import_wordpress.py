from wagtail.core.models import Page

from import_wordpress.parser import parse_xml_file

# delete all pages
Page.objects.all().exclude(slug="home").exclude(slug="root").delete()

# Parse XML
parse_xml_file()
