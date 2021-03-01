from datetime import datetime
import os

from django.conf import settings
from django.test import TestCase

from import_wordpress.parser.main import parse_xml_file
from news.models import Comment
from user.models import User


class TestBlockContent(TestCase):
    def test_comments_are_created(self):
        self.assertEqual(Comment.objects.count(), 0)

        xml_file = os.path.join(
            settings.BASE_DIR,
            "import_wordpress/test/wordpress_test.xml",
        )
        parse_xml_file(xml_file)

        self.assertEqual(Comment.objects.count(), 6)

        earliest_comment_date = datetime.strptime(
            "2021-02-02 12:21:37", "%Y-%m-%d %H:%M:%S"
        )

        earliest_comment = Comment.objects.order_by("posted_date").first()

        self.assertEqual(
            earliest_comment_date,
            earliest_comment.posted_date,
        )


class TestUsers(TestCase):
    def test_users_created(self):
        self.assertEqual(User.objects.count(), 0)

        xml_file = os.path.join(
            settings.BASE_DIR,
            "import_wordpress/test/wordpress_test.xml",
        )
        parse_xml_file(xml_file)

        self.assertEqual(User.objects.count(), 2)


class TestNewsCategories(TestCase):
    def test_users_created(self):
        self.assertEqual(User.objects.count(), 0)

        xml_file = os.path.join(
            settings.BASE_DIR,
            "import_wordpress/test/wordpress_test.xml",
        )
        parse_xml_file(xml_file)

        self.assertEqual(User.objects.count(), 2)
