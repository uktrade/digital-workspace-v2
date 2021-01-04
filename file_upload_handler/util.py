import logging

from django.conf import settings


logger = logging.getLogger(__name__)


def check_required_setting(setting_key):
    if getattr(settings, setting_key, None) is None:
        # Nb cannot throw exception here because of
        # Django bootstrap order of play
        logger.error(
            f"Cannot process file uploads, a required setting, "
            f"'{setting_key}' for Django S3 uploader is missing"
        )
        return None

    return getattr(settings, setting_key)