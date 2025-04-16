from docx.image.image import Image
from wagtail_content_import.mappers import converters


class ImageConverter(converters.ImageConverter):
    def __call__(self, *args, **kwargs):
        response = super().__call__(*args, **kwargs)

        return (
            response[0],
            {
                "image": response[1],
                "isdecorative": False,
                "alt": "",
                "caption": "",
            },
        )

    def fetch_image(self, image: Image) -> tuple[str, bytes]:
        return image.filename, image.blob
