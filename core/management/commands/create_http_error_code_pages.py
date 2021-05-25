from datetime import datetime

from django.core.management.base import BaseCommand

from wagtail.core.models import Page

from content.models import ContentPage


class Command(BaseCommand):
    help = "Create 404, 500, 403 and 400 pages"

    def handle(self, *args, **options):
        home_page = Page.objects.filter(slug="home").first()

        response_codes = 404, 500, 403, 400

        for response_code in response_codes:
            page = ContentPage(
                title=f"{response_code} Error",
                slug=f"{response_code}",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=False,
                depth=1,
            )

            home_page.add_child(instance=page)
            home_page.save()
            page.save_revision().publish()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created page for response code '{response_code}'"
                )
            )
