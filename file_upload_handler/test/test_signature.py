from django.test import TestCase

from file_upload_handler.signature import sign, verify


class VerifySignatureTestCase(TestCase):
    def test_signature(self):
        test_string = "Test foo"
        signed = sign(test_string.encode())

        self.assertTrue(verify(test_string.encode(), signed))
