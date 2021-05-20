from PIL import Image
from django.core.files.uploadedfile import UploadedFile


class ImageService:
    @staticmethod
    def crop_image(
        image_file: UploadedFile, x: int, y: int, width: int, height: int
    ) -> Image:
        image = Image.open(image_file)
        cropped_image = image.crop((x, y, x + width, y + height))

        return cropped_image
