from django.test import TestCase
from content.models import ContentPage


class ContentPageTestCase(TestCase):
    # def setUp(self):
    #     Animal.objects.create(name="lion", sound="roar")
    #     Animal.objects.create(name="cat", sound="meow")

    def test_excluded_and_pinned_created(self):
        content_page = ContentPage(

        )
