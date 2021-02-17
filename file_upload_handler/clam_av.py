import json
import logging
import pathlib
from base64 import b64encode
from http.client import HTTPConnection, HTTPSConnection

from django.conf import settings
from django.core.files.uploadhandler import FileUploadHandler, UploadFileException

from file_upload_handler.models import ScannedFile
from file_upload_handler.util import check_required_setting


logger = logging.getLogger(__name__)


CHUNK_SIZE = 5 * 1024 * 1024

# Clam AV
CLAM_AV_USERNAME = check_required_setting("CLAM_AV_USERNAME")
CLAM_AV_PASSWORD = check_required_setting("CLAM_AV_PASSWORD")
CLAM_AV_URL = check_required_setting("CLAM_AV_URL")
CLAM_PATH = getattr(settings, "CLAM_PATH", "/v2/scan-chunked")
CLAM_AV_IGNORE_EXTENSIONS = getattr(settings, "CLAM_AV_IGNORE_EXTENSIONS", {})


class VirusFoundInFileException(UploadFileException):
    pass


class AntiVirusServiceErrorException(UploadFileException):
    pass


class MalformedAntiVirusResponseException(UploadFileException):
    pass


class ClamAVFileUploadHandler(FileUploadHandler):
    chunk_size = CHUNK_SIZE
    skip_av_check = False

    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        extension = pathlib.Path(self.file_name).suffix

        if extension in CLAM_AV_IGNORE_EXTENSIONS:
            self.skip_av_check = True
            return

        self.av_conn = HTTPSConnection(
            host=CLAM_AV_URL,
        )

        credentials = b64encode(
            bytes(
                f"{CLAM_AV_USERNAME}:{CLAM_AV_PASSWORD}",
                encoding="utf8",
            )
        ).decode("ascii")

        self.av_conn.connect()
        self.av_conn.putrequest("POST", CLAM_PATH)
        self.av_conn.putheader("Content-Type", self.content_type)
        self.av_conn.putheader("Authorization", f"Basic {credentials}")
        self.av_conn.putheader("Transfer-encoding", "chunked")
        self.av_conn.endheaders()

    def receive_data_chunk(self, raw_data, start):
        if not self.skip_av_check:
            self.av_conn.send(hex(len(raw_data))[2:].encode("utf-8"))
            self.av_conn.send(b"\r\n")
            self.av_conn.send(raw_data)
            self.av_conn.send(b"\r\n")

        return raw_data

    def file_complete(self, file_size):
        if self.skip_av_check:
            return None

        self.av_conn.send(b"0\r\n\r\n")

        resp = self.av_conn.getresponse()
        response_content = resp.read()

        scanned_file = ScannedFile()

        if resp.status != 200:
            scanned_file.av_passed = False
            scanned_file.av_reason = "Non 200 response from AV server"
            scanned_file.save()

            raise AntiVirusServiceErrorException(
                f"Non 200 response from anti virus service, content: {response_content}"
            )
        else:
            json_response = json.loads(response_content)

            if "malware" not in json_response:
                scanned_file.av_passed = False
                scanned_file.av_reason = "Malformed response from AV server"
                scanned_file.save()

                raise MalformedAntiVirusResponseException()

            if json_response["malware"]:
                scanned_file.av_passed = False
                scanned_file.av_reason = json_response["reason"]
                scanned_file.save()
                logger.error(
                    f"Malware found in user uploaded file "
                    f"'{self.file_name}', exiting upload process"
                )
                raise VirusFoundInFileException()

            scanned_file.av_passed = True
            scanned_file.save()

            # We are using 'content_type_extra' as the a means of making
            # the results available to following file handlers

            #  TODO - put in a PR to Django project to allow file_complete
            # to return objects and not break out of file handler loop
            if not hasattr(self.content_type_extra, "clam_av_results"):
                self.content_type_extra["clam_av_results"] = []

            self.content_type_extra["clam_av_results"].append(
                {
                    "file_name": self.file_name,
                    "av_passed": True,
                    "scanned_at": scanned_file.scanned_at,
                }
            )

            return None
