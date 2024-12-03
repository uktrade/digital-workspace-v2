from django.test import TestCase

from peoplefinder.templatetags.email_word_break import email_word_break


class TestEmailWordBreak(TestCase):
    def test_standard_departmental_email(self):
        email = "name.surname@businessandtrade.gov.uk"
        expected = "name<wbr>.surname<wbr>@businessandtrade<wbr>.gov.uk"
        self.assertEqual(email_word_break(email), expected)

    def test_external_email(self):
        email = "name.surname@example.com"
        expected = "name<wbr>.surname<wbr>@example.com"
        self.assertEqual(email_word_break(email), expected)

    def test_user_without_dots(self):
        email = "name@businessandtrade.gov.uk"
        expected = "name<wbr>@businessandtrade<wbr>.gov.uk"
        self.assertEqual(email_word_break(email), expected)

    # def test_value_is_none(self):
    #     self.assertEqual(email_word_break(None), None)

    # def test_value_is_integer(self):
    #     self.assertEqual(email_word_break(123), 123)

    # def test_html_escaping(self):
    #     unsafe_input = "<script>alert('xss')</script>@businessandtrade.gov.uk"
    #     expected = (
    #         "&lt;script&gt;alert('xss')&lt;/script&gt;@businessandtrade<wbr>.gov.uk"
    #     )
    #     self.assertEqual(email_word_break(unsafe_input), expected)



    def test_to_be_separated(self):
        email = "name@example.com"
        expected = "name@<wbr>example<wbr>.com"
        self.assertEqual(email_word_break(email), expected)
        
        email = "name.surname@example.com"
        expected = "name<wbr>.surname@<wbr>example<wbr>.com"
        self.assertEqual(email_word_break(email), expected)
        
        email = "name.middle.surname@example.com"
        expected = "name<wbr>.middle<wbr>.surname@<wbr>example<wbr>.com"
        self.assertEqual(email_word_break(email), expected)
        
        email = "name.middle.second-middle.surname@example.com"
        expected = "name<wbr>.middle<wbr>.second-<wbr>middle<wbr>.surname@<wbr>example<wbr>.com"
        self.assertEqual(email_word_break(email), expected)
        
        email = "name@subdomain.example.com"
        expected = "name@<wbr>subdomain<wbr>.example<wbr>.com"
        self.assertEqual(email_word_break(email), expected)
        
        email = "areallylongnamemiddlesurname@example.com"
        expected = "areallylon<wbr>gnamemiddl<wbr>esurname@<wbr>example<wbr>.com"
        self.assertEqual(email_word_break(email), expected)
        
        email = "name@thisisareallylongdomainnametoconfusethetest.com"
        expected = "name@<wbr>thisisarea<wbr>llylongdom<wbr>ainnametoc<wbr>onfusethet<wbr>est<wbr>.com"
        self.assertEqual(email_word_break(email), expected)
