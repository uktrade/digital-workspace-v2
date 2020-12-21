import requests
from io import BytesIO
import boto3

from django import forms
from django.conf import settings

#from wagtail.admin import widgets
#from wagtail.images.forms import BaseImageForm


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


def get_s3_file_body(file_name):
    s3 = boto3.resource(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    obj = s3.Object(
        settings.AWS_STORAGE_BUCKET_NAME,
        file_name,
    )
    data = obj.get()['Body'].read()
    return BytesIO(data)


# class CustomImageForm(BaseImageForm):
#     class Meta:
#         # set the 'file' widget to a FileInput rather than the default ClearableFileInput
#         # so that when editing, we don't get the 'currently: ...' banner which is
#         # a bit pointless here
#         widgets["file"] = forms.FileInput()
