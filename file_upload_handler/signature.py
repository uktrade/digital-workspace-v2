from hashlib import blake2b
from hmac import compare_digest

from file_upload_handler.util import check_required_setting

AUTH_SIZE = 16


def sign(to_sign):
    secret_key = check_required_setting("AV_SIGNATURE_SECRET_KEY")
    hashed = blake2b(
        digest_size=AUTH_SIZE,
        key=bytes(secret_key),
    )
    hashed.update(to_sign)
    return hashed.hexdigest()


def verify(to_verify, sig):
    signed = sign(to_verify)
    return compare_digest(signed, sig)
