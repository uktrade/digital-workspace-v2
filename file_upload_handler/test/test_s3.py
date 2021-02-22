import concurrent.futures
from datetime import datetime
from unittest.mock import MagicMock, call, patch

from django.test import TestCase
from django.test.client import RequestFactory

from file_upload_handler.s3 import (
    S3FileUploadHandler,
    ThreadedS3ChunkUploader,
)


class S3FileHandlerTestCase(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.request()

    def create_s3_handler(self):
        self.s3_file_handler = S3FileUploadHandler(
            request=self.request,
        )
        self.s3_file_handler.new_file(
            "file",
            "file.txt",
            "text/plain",
            100,
            content_type_extra=None,
        )

    @patch("file_upload_handler.s3.boto3_client")
    @patch("file_upload_handler.s3.ThreadedS3ChunkUploader")
    def test_init_connection(self, thread_pool, boto3_client):
        self.s3_file_handler = S3FileUploadHandler(
            request=self.request,
        )
        self.s3_file_handler.new_file(
            "file",
            "file.txt",
            "text/plain",
            100,
            content_type_extra=None,
        )

        self.s3_file_handler.s3_client.create_multipart_upload.assert_called_once()

        thread_pool.assert_called_once()

    @patch("file_upload_handler.s3.boto3_client")
    def test_chunk_is_received(self, client):
        self.create_s3_handler()
        self.s3_file_handler.executor = MagicMock()
        self.s3_file_handler.receive_data_chunk(
            b"test",
            0,
        )
        # Check that we started to send data
        self.s3_file_handler.executor.mock_calls[0] = call.send(b"4")

    @patch("file_upload_handler.s3.boto3_client")
    @patch("file_upload_handler.s3.S3Boto3Storage")
    @patch("file_upload_handler.s3.S3Boto3StorageFile")
    def test_addition_of_av_header(self, storage_file, storage, client):
        self.create_s3_handler()

        # Add content_type_extra which would have been added by file handler processor
        self.s3_file_handler.content_type_extra = {"clam_av_results": []}
        self.s3_file_handler.content_type_extra["clam_av_results"].append(
            {"file_name": "file.txt", "av_passed": True, "scanned_at": datetime.now()}
        )

        # Return ETag from mock so signature can be created
        e_tag = "Test..."

        self.s3_file_handler.s3_client.head_object = MagicMock()
        self.s3_file_handler.s3_client.head_object.return_value = {
            "ETag": e_tag,
        }

        self.s3_file_handler.file_complete(0)

        # copy_object should have been called twice,
        # the second time to add the AV metadata
        self.assertEqual(
            self.s3_file_handler.s3_client.copy_object.call_count,
            2,
        )

        second_copy_obj_call_list = (
            self.s3_file_handler.s3_client.copy_object.call_args_list[1][1]
        )

        self.assertTrue("Metadata" in second_copy_obj_call_list)

        self.assertTrue("av-passed" in second_copy_obj_call_list["Metadata"])
        self.assertTrue(second_copy_obj_call_list["Metadata"]["av-passed"])


class ThreadedS3ChunkUploaderTestCase(TestCase):
    @patch("file_upload_handler.s3.S3_MIN_PART_SIZE", 10)
    @patch("file_upload_handler.s3.boto3_client")
    def test_add_future_with_body(self, client):
        test_etag = "test"
        client.upload_part.return_value = {"ETag": test_etag}

        threaded_s3_uploader = ThreadedS3ChunkUploader(
            client, "test_bucket", "test_key", "test_upload_id"
        )

        threaded_s3_uploader.add(b"ninebytes")
        self.assertEqual(threaded_s3_uploader.current_queue_size, 9)

        threaded_s3_uploader.client.upload_part.assert_not_called()

        # Push total bytes above min size
        threaded_s3_uploader.add(b"morebytes")
        self.assertEqual(threaded_s3_uploader.current_queue_size, 0)
        self.assertEqual(len(threaded_s3_uploader.futures), 1)

        # Wait for upload threads to complete
        concurrent.futures.wait(
            threaded_s3_uploader.futures, return_when=concurrent.futures.ALL_COMPLETED
        )

        # There should have only been one upload call
        threaded_s3_uploader.client.upload_part.assert_called_once()

        # Check parts is as expected
        parts = threaded_s3_uploader.get_parts()

        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["PartNumber"], 1)
        self.assertEqual(parts[0]["ETag"], test_etag)
