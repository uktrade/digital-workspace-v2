from peoplefinder.templatetags import email_word_break


class TestEmailWordBreak:
    def test_standard_departmental_email(self):
        email = "name.surname@businessandtrade.gov.uk"
        expected = "name<wbr>.surname<wbr>@businessandtrade<wbr>.gov.uk"
        self.assertEqual(email_word_break(email), expected)

    def test_external_email(self):
        email = "name.surname@example.com"
        expected = "name<wbr>.surname@example.com"
        self.asserEqual(email_word_break(email), expected)

    def test_user_without_dots(self):
        email = "name@businessandtrade.gov.uk"
        expected = "name<wbr>@businessandtrade<wbr>.gov.uk"
        self.asserEqual(email_word_break(email), expected)

    def test_value_is_none(self):
        self.asserEqual(email_word_break(None), None)

    def test_value_is_integer(self):
        self.asserEqual(email_word_break(123), 123)

    def test_html_escaping(self):
        unsafe_input = "<script>alert('xss')</script>@businessandtrade.gov.uk"
        expected = (
            "&lt;script&gt;alert('xss')&lt;/script&gt;@businessandtrade<wbr>.gov.uk"
        )
        self.asserEqual(email_word_break(unsafe_input), expected)
