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


def check_required_setting(setting_key):
    if getattr(settings, setting_key, None) is None:
        # Nb cannot throw exception here because of
        # Django bootstrap order of play
        logger.error(
            f"Cannot process file uploads, a required setting, "
            f"'{setting_key}' for Django S3 uploader is missing"
        )
        return None

    return getattr(settings, setting_key)


# AWS
AWS_ACCESS_KEY_ID = check_required_setting("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = check_required_setting("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = check_required_setting("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = getattr(settings, "AWS_REGION", None)
CHUNK_SIZE = 6 * 1024 * 1024

# Clam AV
CLAM_AV_USERNAME = check_required_setting("S3_CHUNK_CLAM_AV_USERNAME")
CLAM_AV_PASSWORD = check_required_setting("S3_CHUNK_CLAM_AV_PASSWORD")
CLAM_AV_URL = check_required_setting("S3_CHUNK_CLAM_AV_URL")
CLAM_PATH = getattr(settings, "S3_CHUNK_CLAM_PATH", '/v2/scan-chunked')

ADD_TIMESTAMP_TO_OBJECT_NAME = getattr(
    settings,
    'ADD_TIMESTAMP_TO_OBJECT_NAME',
    True,
)

if (
    getattr(settings, "DEFAULT_FILE_STORAGE", None) is None or
    settings.DEFAULT_FILE_STORAGE != 'storages.backends.s3boto3.S3Boto3Storage'
):
    # Nb cannot throw exception here because of
    # Django bootstrap order of play
    logger.error(
        "You must use S3Boto3Storage with this file handler"
    )


class ChunkReceiver(ABC):
    @abstractmethod
    def receive_data_chunk(self, chunk):
        pass

    @abstractmethod
    def validate(self):
        pass

    @abstractmethod
    def complete(self):
        pass

    @abstractmethod
    def abort(self):
        pass


class S3ChunkUpload(ChunkReceiver):
    def __init__(self, content_type):
        self.content_type = content_type

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
        self.parts = []
        self.part_number = 1
        self.s3_key = f"chunk_upload_{str(uuid.uuid4())}"
        self.multipart = self.s3_client.create_multipart_upload(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=self.s3_key,
            ContentType=self.content_type,
        )
        self.upload_id = self.multipart['UploadId']

    def receive_data_chunk(self, chunk):
        pass
        # print("len(chunk)")
        # print(len(chunk))
        #
        # result = self.s3_client.upload_part(
        #     Bucket=AWS_STORAGE_BUCKET_NAME,
        #     Key=self.s3_key,
        #     PartNumber=self.part_number,
        #     UploadId=self.upload_id,
        #     Body=chunk,
        #     ContentLength=len(chunk),
        # )
        # self.parts.append((self.part_number, result))
        # self.part_number += 1

    def get_parts(self):
        return [{
            'PartNumber': part[0],
            'ETag': part[1]['ETag'],
            } for part in self.parts
        ]

    def validate(self):
        pass

    def complete(self, new_file_name):
        pass
        # parts = self.get_parts()
        #
        # self.s3_client.complete_multipart_upload(
        #     Bucket=AWS_STORAGE_BUCKET_NAME,
        #     Key=self.s3_key,
        #     UploadId=self.upload_id,
        #     MultipartUpload={
        #         'Parts': parts
        #     },
        # )
        #
        # self.s3_client.copy_object(
        #     Bucket=AWS_STORAGE_BUCKET_NAME,
        #     CopySource=f"{AWS_STORAGE_BUCKET_NAME}/{self.s3_key}",
        #     Key=new_file_name,
        #     Metadata={
        #         "clam-av-result": "passed",
        #     },
        #     ContentType=self.content_type,
        #     MetadataDirective='REPLACE',
        # )
        # self.s3_client.delete_object(
        #     Bucket=AWS_STORAGE_BUCKET_NAME,
        #     Key=self.s3_key,
        # )

    def abort(self):
        try:
            self.s3_client.abort_multipart_upload(
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=self.s3_key,
                UploadId=self.upload_id,
            )
        except Exception as ex:
            raise AbortS3UploadException(
                "Error when aborting S3 multipart upload"
            ) from ex


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


CHUNK_RECEIVERS = [
    S3ChunkUpload,
    ClamAVChunkUpload,
]


class S3FileUploadHandler(FileUploadHandler):
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
