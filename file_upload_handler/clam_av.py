from base64 import b64encode
import boto3
import json
import logging
import pathlib
import uuid
from concurrent.futures import ThreadPoolExecutor

from http import client as http_client

from django.utils import timezone
from django.core.files.uploadhandler import FileUploadHandler, UploadFileException
from storages.backends.s3boto3 import S3Boto3StorageFile, S3Boto3Storage
from django.conf import settings

from django.core.files.uploadhandler import SkipFile

from file_upload_handler.util import check_required_setting


logger = logging.getLogger(__name__)


CHUNK_SIZE = 5 * 1024 * 1024

# Clam AV
CLAM_AV_USERNAME = check_required_setting("S3_CHUNK_CLAM_AV_USERNAME")
CLAM_AV_PASSWORD = check_required_setting("S3_CHUNK_CLAM_AV_PASSWORD")
CLAM_AV_URL = check_required_setting("S3_CHUNK_CLAM_AV_URL")
CLAM_PATH = getattr(settings, "S3_CHUNK_CLAM_PATH", '/v2/scan-chunked')


class VirusFoundInFileException(UploadFileException):
    pass


class AntiVirusServiceErrorException(UploadFileException):
    pass


class MalformedAntiVirusResponseException(UploadFileException):
    pass


class ClamAVFileUploadHandler(FileUploadHandler):
    chunk_size = CHUNK_SIZE

    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)

        self.av_conn = http_client.HTTPConnection(
            CLAM_AV_URL,
        )

        credentials = b64encode(
            bytes(
                f"{CLAM_AV_USERNAME}:{CLAM_AV_PASSWORD}",
                encoding='utf8',
            )
        ).decode("ascii")

        self.av_conn.connect()
        self.av_conn.putrequest('POST', CLAM_PATH)
        self.av_conn.putheader('Content-Type', self.content_type)
        self.av_conn.putheader('Authorization', f'Basic {credentials}')
        self.av_conn.putheader('Transfer-encoding', "chunked")
        self.av_conn.endheaders()

    def receive_data_chunk(self, raw_data, start):
        self.av_conn.send(hex(len(raw_data))[2:].encode('utf-8'))
        self.av_conn.send(b'\r\n')
        self.av_conn.send(raw_data)
        self.av_conn.send(b'\r\n')

        return raw_data

    def handle_raw_input(
        self,
        input_data,
        META,
        content_length,
        boundary,
        encoding=None,
    ):
        self.request = input_data
        self.META = META
        self.content_len = content_length

    def file_complete(self, file_size):
        self.av_conn.send(b'0\r\n\r\n')
        resp = self.av_conn.getresponse()
        response_content = resp.read()

        raise SkipFile()


        if resp.status != 200:
            logger.error(
                f"Non 200 response from anti virus service, content: {response_content}"
            )
            self.abort()
            raise AntiVirusServiceErrorException
        else:
            json_response = json.loads(response_content)

            if "malware" not in json_response:
                raise MalformedAntiVirusResponseException()

            if json_response["malware"]:
                raise VirusFoundInFileException()

            return None

    def upload_complete(self):
        """
        Signal that the upload is complete. Subclasses should perform cleanup
        that is necessary for this handler.
        """
        # from django.core.exceptions import ValidationError
        # raise ValidationError("ERROR....")
        pass

    def upload_interrupted(self):
        """
        Signal that the upload was interrupted. Subclasses should perform
        cleanup that is necessary for this handler.
        """
        from django.core.exceptions import ValidationError
        raise ValidationError("ERROR....")
        pass