from unittest.mock import patch, Mock

from django.test import (
    TestCase,
)

from import_wordpress.utils.helpers import add_paragraph_tags


class Helpers(TestCase):
    def test_add_paragraph_tags(self):
        text = """Paragraph of text without tag.
            
        Another paragraph of text without tag.
        
        Yet another paragraph of text without tag.
        """
        with_paras = add_paragraph_tags(text)

        # TODO - add assertions

        print(with_paras)

        assert False
