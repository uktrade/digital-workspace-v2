from django.test import TestCase

from file_upload_handler.signature import sign, verify


class VerifySignatureTestCase(TestCase):
    test_string = "Test foo"
    signed = sign(test_string.encode())

    assert verify(test_string.encode(), signed)
