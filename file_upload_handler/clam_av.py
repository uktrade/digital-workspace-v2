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

from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class VirusFoundInFileException(UploadFileException):
    pass


class AntiVirusServiceErrorException(UploadFileException):
    pass


class AbortS3UploadException(UploadFileException):
    pass


class MalformedAntiVirusResponseException(UploadFileException):
    pass


class ErrorProcessingChunkException(UploadFileException):
    pass




class ClamAVChunkUpload(ChunkReceiver):
    def __init__(self, content_type):
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
        self.av_conn.putheader('Content-Type', content_type)
        self.av_conn.putheader('Authorization', f'Basic {credentials}')
        self.av_conn.putheader('Transfer-encoding', "chunked")
        self.av_conn.endheaders()

    def receive_data_chunk(self, chunk):
        self.av_conn.send(hex(len(chunk))[2:].encode('utf-8'))
        self.av_conn.send(b'\r\n')
        self.av_conn.send(chunk)
        self.av_conn.send(b'\r\n')

    def validate(self):
        self.av_conn.send(b'0\r\n\r\n')
        resp = self.av_conn.getresponse()
        response_content = resp.read()

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

    def complete(self, new_file_name):
        pass

    def abort(self):
        pass


class ClamAVFileUploadHandler(FileUploadHandler):
    chunk_size = CHUNK_SIZE

    def __init__(self, request=None):
        super().__init__(request)
        self.receivers = []
        self.new_file_name = ""

    def new_file(self, *args, **kwargs):
        try:
            super().new_file(*args, **kwargs)
            extension = pathlib.Path(self.file_name).suffix
            time_stamp = f'{timezone.now().strftime("%Y%m%d%H%M%S")}'
            self.new_file_name = f"{self.file_name.replace(extension, '')}_{time_stamp}{extension}"

            for receiver in CHUNK_RECEIVERS:
                self.receivers.append(
                    receiver(
                        self.content_type,
                    )
                )

        except Exception as ex:
            raise UploadFileException(
                "Error setting up chunk receivers"
            ) from ex

    def receive_data_chunk(self, raw_data, start):
        try:
            for receiver in self.receivers:
                receiver.receive_data_chunk(raw_data)
        except Exception as ex:
            for receiver in self.receivers:
                receiver.abort()
            raise ErrorProcessingChunkException(
                "An exception occurred when processing a file chunk"
            ) from ex

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
        try:
            for receiver in self.receivers:
                receiver.validate()

            for receiver in self.receivers:
                receiver.complete(self.new_file_name)

            storage = S3Boto3Storage()
            file = S3Boto3StorageFile(self.new_file_name, 'rb', storage)
            file.content_type = self.content_type

            file.file_size = file_size
            file.close()

            return file
        except Exception as ex:
            for receiver in self.receivers:
                receiver.abort()

            raise UploadFileException(
                "An exception occurred when attempting to upload and scan a file"
            ) from ex