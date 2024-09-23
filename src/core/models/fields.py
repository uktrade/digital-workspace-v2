from django.db.models import URLField


class URLField(URLField):
    max_length = 2048
