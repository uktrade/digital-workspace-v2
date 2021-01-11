from hashlib import blake2b
from hmac import compare_digest

from django.conf import settings

SECRET_KEY = settings.AV_SIGNATURE_SECRET_KEY.encode()
AUTH_SIZE = 16


def sign(to_sign):
    hashed = blake2b(digest_size=AUTH_SIZE, key=SECRET_KEY)
    hashed.update(to_sign)
    return hashed.hexdigest()


def verify(to_verify, sig):
    signed = sign(to_verify)
    return compare_digest(signed, sig)
