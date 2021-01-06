from django.test import TestCase, override_settings
from file_upload_handler.clam_av import ClamAVFileUploadHandler
from django.test.client import RequestFactory
from unittest.mock import patch

from django.conf import settings


test_clam_av_url = "http://test.com"


@override_settings(CLAM_AV_URL=test_clam_av_url)
class ClamAVFileHandlerTestCase(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.request()

    def create_av_handler(self):
        print("FROM TEST CLAM_AV_URL", flush=True)
        print(settings.CLAM_AV_URL, flush=True)

        self.clam_av_file_handler = ClamAVFileUploadHandler(
            request=self.request,
        )
        self.clam_av_file_handler.new_file(
            "file",
            "file.txt",
            "text/plain",
            100,
            content_type_extra=None,
        )

    @patch('file_upload_handler.clam_av.http_client.HTTPConnection')
    def test_init_connection(self, http_connection):
        self.create_av_handler()

        assert http_connection.assert_called_once_with(
            test_clam_av_url,
        )

    @override_settings(CLAM_AV_IGNORE_EXTENSIONS={'txt', })
    @patch('file_upload_handler.clam_av.http_client.HTTPConnection')
    def test_no_connection_if_ext_exempt(self, http_connection):
        self.create_av_handler()

        assert not http_connection.assert_called()

    @override_settings(CLAM_AV_IGNORE_EXTENSIONS={'txt', })
    @patch('file_upload_handler.clam_av.http_client.HTTPConnection')
    def test_no_chunk_processing_if_ext_exempt(self, http_connection):
        self.create_av_handler()

        self.clam_av_file_handler.receive_data_chunk(
            b"test_chunk",
            10,
        )

        assert not http_connection.send.assert_called()
