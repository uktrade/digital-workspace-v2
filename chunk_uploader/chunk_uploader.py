from base64 import b64encode
import boto3
import json
import logging
import pathlib
import uuid

from http import client as http_client

from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor
from django.core.files.uploadhandler import FileUploadHandler, UploadFileException
from storages.backends.s3boto3 import S3Boto3StorageFile, S3Boto3Storage
from django.conf import settings


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
S3_MIN_PART_SIZE = 5 * 1024 * 1024

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


s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)


class ThreadedS3ChunkUploader(ThreadPoolExecutor):
    def __init__(self, key, upload_id, max_workers=None):
        max_workers = max_workers or 10
        self.key = key
        self.upload_id = upload_id
        self.part_number = 0
        self.parts = []
        self.queue = []
        self.current_queue_size = 0
        super().__init__(max_workers=max_workers)

    def add(self, chunk):
        if chunk:
            _content_length = len(chunk)
            self.queue.append(chunk)
            self.current_queue_size += _content_length

        if not chunk or self.current_queue_size > S3_MIN_PART_SIZE:
            self.part_number += 1

            body = self.drain_queue()
            future = self.submit(
                s3_client.upload_part,
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=self.key,
                PartNumber=self.part_number,
                UploadId=self.upload_id,
                Body=body,
                ContentLength=len(body),
            )
            self.parts.append((self.part_number, future))
            logger.debug('Prepared part %s', self.part_number)

    def drain_queue(self):
        body = b''.join(self.queue)
        self.queue = []
        self.current_queue_size = 0
        return body

    def get_parts(self):
        return [{
            'PartNumber': part[0],
            'ETag': part[1].result()['ETag'],
            } for part in self.parts
        ]


def generate_object_key(file_name):
    extension = pathlib.Path(file_name).suffix
    time_stamp = f'{timezone.now().strftime("%Y%m%d%H%M%S")}'
    return f"{file_name.replace(extension, '')}_{time_stamp}{extension}"


class S3FileUploadHandler(FileUploadHandler):
    def connect_av(self):
        credentials = b64encode(
            bytes(
                f"{CLAM_AV_USERNAME}:{CLAM_AV_PASSWORD}",
                encoding='utf8',
            )
        ).decode("ascii")

        self.av_conn.connect()
        self.av_conn.putrequest('POST', CLAM_PATH)
        self.av_conn.putheader('Content-Type', self.content_type)
        #self.av_conn.putheader('Content-Length', str(self.c_len))
        self.av_conn.putheader('Authorization', f'Basic {credentials}')
        self.av_conn.putheader('Transfer-encoding', "chunked")

        self.av_conn.endheaders()



    def new_file(self, *args, **kwargs):
        try:
            super().new_file(*args, **kwargs)

            self.new_file_name = generate_object_key(self.file_name)
            self.av_conn = http_client.HTTPConnection(
                CLAM_AV_URL,
                #timeout=100,
            )
            self.parts = []
            self.s3_key = f"chunk_upload_{str(uuid.uuid4())}"
            self.multipart = s3_client.create_multipart_upload(
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=self.s3_key,
                ContentType=self.content_type,
            )
            self.upload_id = self.multipart['UploadId']
            self.executor = ThreadedS3ChunkUploader(
                key=self.s3_key,
                upload_id=self.upload_id
            )
            self.connect_av()
        except Exception as ex:
            raise UploadFileException() from ex

    def receive_data_chunk(self, raw_data, start):
        try:
            self.executor.add(raw_data)
            self.send_av_chunk(raw_data)
        except Exception as ex:
            self.abort()
            raise ErrorProcessingChunkException(
                "An exception occurred when processing a file chunk"
            ) from ex

    def send_av_chunk(self, chunk):
        test = len(chunk)
        self.av_conn.send(hex(len(chunk))[2:].encode('utf-8'))
        self.av_conn.send(b'\r\n')
        self.av_conn.send(chunk)
        self.av_conn.send(b'\r\n')

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
        self.content_length = content_length
        self.c_len = content_length

    def file_complete(self, file_size):
        try:
            self.executor.add(None)
            # Send closing chunk

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

            parts = self.executor.get_parts()

            s3_client.complete_multipart_upload(
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=self.s3_key,
                UploadId=self.upload_id,
                MultipartUpload={
                    'Parts': parts
                },
            )

            self.executor.shutdown()
            self.replace_s3_file()

            storage = S3Boto3Storage()
            file = S3Boto3StorageFile(self.new_file_name, 'rb', storage)
            file.original_name = self.file_name
            file.content_type = self.content_type

            file.file_size = file_size
            file.close()

            return file
        except Exception as ex:
            self.abort()
            raise UploadFileException(
                "An exception occurred when attempting to upload and scan a file"
            ) from ex

    def replace_s3_file(self):
        # head_object = s3_client.head_object(
        #     Bucket=AWS_STORAGE_BUCKET_NAME,
        #     Key=self.s3_key,
        # )
        # head_object["ResponseMetadata"]["HTTPHeaders"].update(
        #     {'Clam-AV-result': 'passed'}
        # )
        s3_client.copy_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            CopySource=f"{AWS_STORAGE_BUCKET_NAME}/{self.s3_key}",
            Key=self.new_file_name,
            Metadata={
                "clam-av-result": "passed",
            },
            ContentType=self.content_type,
            MetadataDirective='REPLACE',
        )
        s3_client.delete_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=self.s3_key,
        )

    def abort(self):
        try:
            s3_client.abort_multipart_upload(
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=self.s3_key,
                UploadId=self.upload_id,
            )
        except Exception as ex:
            raise AbortS3UploadException(
                "Error when aborting S3 multipart upload"
            ) from ex
