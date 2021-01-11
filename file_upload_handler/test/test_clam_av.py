from django.test import TestCase
from file_upload_handler.clam_av import ClamAVFileUploadHandler
from django.test.client import RequestFactory
from unittest.mock import Mock, MagicMock, patch, call
from file_upload_handler.models import ScannedFile
from file_upload_handler.clam_av import (
    AntiVirusServiceErrorException,
    MalformedAntiVirusResponseException,
    VirusFoundInFileException,
)

test_clam_av_url = "http://test.com"


# Need to directly override settings rather than using
# override_settings as it does not work with logic used
class ClamAVFileHandlerTestCase(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.request()

    @patch('file_upload_handler.clam_av.CLAM_AV_URL', test_clam_av_url)
    def create_av_handler(self):
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

    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_init_connection(self, http_connection):
        self.create_av_handler()

        # Check that we made a connection
        http_connection.mock_calls[0] = call(test_clam_av_url)

    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_chunk_is_received(self, http_connection):
        self.create_av_handler()
        self.clam_av_file_handler.av_conn = MagicMock()
        self.clam_av_file_handler.receive_data_chunk(
            b'test',
            0,
        )
        # Check that we started to send data
        self.clam_av_file_handler.av_conn.mock_calls[0] = call.send(b'4')

    @patch('file_upload_handler.clam_av.CLAM_AV_IGNORE_EXTENSIONS', {'.txt', })
    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_no_connection_if_ext_exempt(self, http_connection):
        self.create_av_handler()

        # Check that we did not make a connection
        assert len(http_connection.mock_calls) == 0

    @patch('file_upload_handler.clam_av.CLAM_AV_IGNORE_EXTENSIONS', {'.txt', })
    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_no_chunk_processing_if_ext_exempt(self, http_connection):
        self.create_av_handler()
        self.clam_av_file_handler.av_conn = MagicMock()
        self.clam_av_file_handler.receive_data_chunk(
            b'test',
            0,
        )

        # Check that we did not process chunk
        assert len(self.clam_av_file_handler.av_conn.mock_calls) == 0

    @patch('file_upload_handler.clam_av.CLAM_AV_IGNORE_EXTENSIONS', {'.txt', })
    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_no_virus_check_ext_exempt(self, http_connection):
        self.create_av_handler()
        self.clam_av_file_handler.av_conn = MagicMock()
        self.clam_av_file_handler.file_complete(0)

        # Check that we did send to AV
        assert len(self.clam_av_file_handler.av_conn.mock_calls) == 0

    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_file_complete_with_non_200_response_from_av_service(self, http_connection):
        self.create_av_handler()

        self.clam_av_file_handler.av_conn.getresponse.return_value = Mock(
            status=403,
        )

        with self.assertRaises(AntiVirusServiceErrorException):
            self.clam_av_file_handler.file_complete(0)

        assert ScannedFile.objects.count() == 1
        assert ScannedFile.objects.first().av_passed is False

    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_file_complete_malformed_av_response(self, http_connection):
        self.create_av_handler()

        self.clam_av_file_handler.av_conn.getresponse.return_value = Mock(
            status=200,
            read=Mock(return_value='{ "malformed": false }')
        )

        with self.assertRaises(MalformedAntiVirusResponseException):
            self.clam_av_file_handler.file_complete(0)

        assert ScannedFile.objects.count() == 1
        assert ScannedFile.objects.first().av_passed is False

    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_file_complete_virus_found(self, http_connection):
        self.create_av_handler()

        self.clam_av_file_handler.av_conn.getresponse.return_value = Mock(
            status=200,
            read=Mock(return_value='{ "malware": true, "reason": "test" }')
        )

        with self.assertRaises(VirusFoundInFileException):
            self.clam_av_file_handler.file_complete(0)

        assert ScannedFile.objects.count() == 1
        assert ScannedFile.objects.first().av_passed is False

    @patch('file_upload_handler.clam_av.HTTPConnection')
    def test_file_complete_no_virus_found(self, http_connection):
        self.create_av_handler()

        # Add content_type_extra which would have been added by file handler processor
        self.clam_av_file_handler.content_type_extra = {}

        self.clam_av_file_handler.av_conn.getresponse.return_value = Mock(
            status=200,
            read=Mock(return_value='{ "malware": false, "reason": "test" }')
        )

        self.clam_av_file_handler.file_complete(0)

        assert ScannedFile.objects.count() == 1
        assert ScannedFile.objects.first().av_passed is True

        assert self.clam_av_file_handler.content_type_extra["clam_av_results"][0]["av_passed"] is True
