from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class AssetStorage(S3Boto3Storage):
    # location = settings.AWS_PRIVATE_MEDIA_LOCATION
    # default_acl = 'private'
    # file_overwrite = False
    # custom_domain = False

    """
    Overriding the `url` function to find & replace a dual-stack endpoint in the URL
    """
    def url(self, name, parameters=None, expire=None, http_method=None):
        # Preserve the trailing slash after normalizing the path.
        name = self._normalize_name(self._clean_name(name))
        if expire is None:
            expire = self.querystring_expire

        params = parameters.copy() if parameters else {}
        params['Bucket'] = self.bucket.name
        params['Key'] = name
        url = self.bucket.meta.client.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=expire,
            HttpMethod=http_method,
        )

        return url.replace(
            settings.AWS_STORAGE_BUCKET_NAME,
            settings.AWS_S3_CUSTOM_DOMAIN,
        ).replace(
            ".s3.amazonaws.com",
            "",
        )
