import boto3
import logging

from http import client as http_client

from django.utils.text import slugify
from concurrent.futures import ThreadPoolExecutor
from django.core.files.uploadhandler import FileUploadHandler, UploadFileException
from storages.backends.s3boto3 import S3Boto3StorageFile, S3Boto3Storage
from django.conf import settings


logger = logging.getLogger(__name__)


# AWS
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID  # Required
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY  # Required
AWS_REGION = settings.AWS_REGION
S3_MIN_PART_SIZE = 5 * 1024 * 1024
AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME

# ClamAV REST endpoint
CLAM_AV_USERNAME = settings.CLAM_AV_USERNAME
CLAM_AV_PASSWORD = settings.CLAM_AV_PASSWORD
CLAM_AV_URL = settings.CLAM_AV_URL
CLAM_PATH = '/v3/scan'

CLAM_AUTH = (
    settings.CLAM_AV_USERNAME,
    settings.CLAM_AV_PASSWORD,
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

    def add(self, body):
        if body:
            content_length = len(body)
            self.queue.append(body)
            self.current_queue_size += content_length

        if not body or self.current_queue_size > S3_MIN_PART_SIZE:
            self.part_number += 1

            _body = self.drain_queue()
            future = self.submit(
                s3_client.upload_part,
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=self.key,
                PartNumber=self.part_number,
                UploadId=self.upload_id,
                Body=_body,
                ContentLength=len(_body),
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
    return slugify(file_name)

from base64 import b64encode


class S3FileUploadHandler(FileUploadHandler):
    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        try:
            self.av_conn = http_client.HTTPConnection(CLAM_AV_URL)
            self.av_conn.connect()

            creds = b64encode(b"app1:letmein").decode("ascii")

            self.av_conn.putrequest('POST', CLAM_PATH)
            self.av_conn.putheader('Content-Type', 'application/octet-stream')
            self.av_conn.putheader('Authorization', f'Basic {creds}')
            # av_conn.putheader('Content-Length', str(total_size))
            self.av_conn.endheaders()

            self.parts = []
            file_name = self.file_name
            self.s3_key = generate_object_key(file_name)
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

            # prepare a storages object as a file placeholder
            self.storage = S3Boto3Storage()
            self.file = S3Boto3StorageFile(self.s3_key, 'w', self.storage)
            self.file.original_name = self.file_name
            self.file.content_type = self.content_type
        except Exception as ex:
            print(ex)
            raise Exception()

    def handle_raw_input(
        self,
        input_data,
        META,
        content_length,
        boundary,
        encoding,
    ):
        self.request = input_data
        self.content_length = content_length
        self.META = META
        return None

    def receive_data_chunk(self, raw_data, start):
        try:
            self.executor.add(raw_data)
            self.av_conn.send(raw_data)
        except Exception as exc:
            self.abort(exc)

    def file_complete(self, file_size):
        self.executor.add(None)

        resp = self.av_conn.getresponse()

        if resp.status != 200:
            raise Exception("Problem checking AV for file")

        parts = self.executor.get_parts()

        s3_client.complete_multipart_upload(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=self.s3_key,
            UploadId=self.upload_id,
            MultipartUpload={
                'Parts': parts
            }
        )
        self.executor.shutdown()
        self.file.file_size = file_size
        self.file.close()
        return self.file

    def abort(self, exception):
        self.file.close()
        self.client.abort_multipart_upload(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=self.s3_key,
            UploadId=self.upload_id,
        )
        raise UploadFileException(exception)


# @app.route("/v3/scan", methods=["POST", "GET"])
# @auth.login_required
# def scan_v2():
#     print('Hello world!', file=sys.stderr)
#
#
#     # if len(request.files) != 1:
#     #     return "Provide a single file", 400
#
#
#
#     try:
#         chunk_size = 4096
#         file_name = "test"# urllib.parse.unquote(filename)
#         #bytes_left = int(request.headers.get('content-length'))
#         file_bytes = io.BytesIO()
#
#         print('Hier....', file=sys.stderr)
#         # with open(file_bytes, 'wb') as file_data:
#         #     chunk_size = 5120
#         #     while bytes_left > 0:
#         #         chunk = request.stream.read(chunk_size)
#         #         file_data.write(chunk)
#         #         bytes_left -= len(chunk)
#
#         while True:
#             print('WTF....', file=sys.stderr)
#             try:
#                 print('WTF....', file=sys.stderr)
#                 chunk = request.stream.read(chunk_size)
#
#                 if len(chunk) == 0:
#                     return
#
#                 print('Wrote chunk...!', file=sys.stderr)
#
#                 file_data.write(chunk)
#             except Exception as ex:
#                 print(ex, file=sys.stderr)
#                 return "Error"
#
#         logger.info("Starting scan for {app_user} of {file_name}".format(
#             app_user=g.current_user,
#             file_name=filename
#         ))
#
#         start_time = timeit.default_timer()
#         resp = cd.instream(file_data)
#         elapsed = timeit.default_timer() - start_time
#
#         status, reason = resp["stream"]
#
#         response = {
#             'malware': False if status == "OK" else True,
#             'reason': reason,
#             'time': elapsed
#         }
#
#         logger.info("Scan v2 for {app_user} of {file_name} complete. Took: {elapsed}. Malware found?: {status}".format(
#             app_user=g.current_user,
#             file_name=file_data.filename,
#             elapsed=elapsed,
#             status=response['malware']
#         ))
#
#         return jsonify(response)
#     except Exception as ex:
#         print('Hier....', file=sys.stderr)
#         return "Error", 500