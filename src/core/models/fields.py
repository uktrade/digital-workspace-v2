from django.db import models


class URLField(models.URLField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 2048)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get("max_length") == 2048:
            del kwargs["max_length"]
        return name, path, args, kwargs
