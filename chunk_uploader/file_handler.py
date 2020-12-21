import logging
import requests

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
)
from django.core.files.uploadhandler import (
    MemoryFileUploadHandler,
    StopUpload,
    UploadFileException,
)


logger = logging.getLogger(__name__)


class UploadFileException(Exception):
    """
    Any error having to do with uploading files.
    """
    pass


class VirusFoundException(UploadFileException):
    def __str__(self):
        return 'A virus was found in the uploaded file.'


def run_anti_virus(file_body):
    # Check file with AV web service
    if settings.IGNORE_ANTI_VIRUS:
        return {'malware': False}

    files = {"file": file_body}

    auth = (
        settings.CLAM_AV_USERNAME,
        settings.CLAM_AV_PASSWORD,
    )
    response = requests.post(
        settings.CLAM_AV_URL,
        auth=auth,
        files=files,
    )

    return response.json()


class VirusCheckFileUploadHandler(MemoryFileUploadHandler):
    def file_complete(self, file_size):
        super().file_complete(file_size)

        # Carry out AV check
        anti_virus_result = run_anti_virus(self.file)
        logger.info("Ran anti virus check")

        #if anti_virus_result["malware"]:
        raise StopUpload()

        return InMemoryUploadedFile(
            file=self.file,
            field_name=self.field_name,
            name=self.file_name,
            content_type=self.content_type,
            size=file_size,
            charset=self.charset,
            content_type_extra=self.content_type_extra
        )
