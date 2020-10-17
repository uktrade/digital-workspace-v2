import os
from datetime import datetime
from bs4 import BeautifulSoup

import xml.etree.ElementTree as element_tree

from django.core.management.base import BaseCommand
from django.conf import settings

namespaces = settings.NAMESPACES

xml_file = os.path.join(settings.BASE_DIR, "wordpress_all.xml")


class Command(BaseCommand):
    help = "List all links present in content"

    def handle(self, *args, **options):
        root = element_tree.parse(xml_file).getroot()

        print("Page URL\tLink URL\tDate published")

        for item_tag in root.find("channel").findall('item'):
            page_url = item_tag.find("link", namespaces).text
            pub_date = item_tag.find("pubDate", namespaces)
            if hasattr(pub_date, "text"):
                # Fri, 17 Jul 2020 10:00:07 +0000
                try:
                    publish_date = datetime.strptime(
                        pub_date.text,
                        '%a, %d %b %Y %H:%M:%S %z',
                    )
                except:
                    continue

            # Check for attachment
            attachment_urls = item_tag.findall("wp:attachment_url", namespaces)

            if len(attachment_urls) > 0:
                attachment_url = attachment_urls[0]
                print(f"attachment\t{attachment_url.text}\t{publish_date}")
                continue

            # # Look in content
            content_tag = item_tag.find("content:encoded", namespaces)

            if content_tag.text:
                soup = BeautifulSoup(content_tag.text, 'html.parser')

                for link in soup.find_all('a'):
                    href = str(link.get('href'))
                    if "https://admin.workspace.trade.gov.uk/wp-content/" in href:
                        print(f"{page_url}\t{link.get('href')}\t{publish_date}")

