
import boto3

from django.conf import settings

s3 = boto3.client('s3')


legacy_domains = [
    'digital-workspace-staging.london.cloudapps.digital',
    'api.workspace.trade.uat.uktrade.io',
    'admin.workspace.trade.uat.uktrade.io',
    'admin.workspace.trade.gov.uk',
    'digital-workspace-dev.london.cloudapps.digital',
    'dit.useconnect.co.uk',
]

asset_domain = "workspace-trade-gov-uk.s3.eu-west-2.amazonaws.com"


def convert_domain(src_value):
    for legacy_domain in legacy_domains:
        src_value = src_value.replace(legacy_domain, asset_domain)

    return src_value


def is_live(status):
    if status == "publish":
        return True


def download_s3_file(file_name):
    s3_response_object = s3.get_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_name,
    )
    object_content = s3_response_object['Body'].read()

    return object_content
