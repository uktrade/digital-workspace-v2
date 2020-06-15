import os

import wpparser

from django.conf import settings

from content.models import ContentPage

xml_file = os.path.join(settings.BASE_DIR, "wordpress.xml")
wp_data = wpparser.parse(xml_file)

for post in wp_data["posts"]:
    print(post)
    # content_page = ContentPage(
    #
    # )
    # content_page.save()
    break  # Break until we have established logic
