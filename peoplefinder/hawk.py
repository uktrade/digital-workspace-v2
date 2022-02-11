import logging

from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import constant_time_compare

from mohawk import Receiver
from mohawk.exc import HawkFail

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


logger = logging.getLogger(__name__)

NO_CREDENTIALS_MESSAGE = 'Authentication credentials were not provided.'
INCORRECT_CREDENTIALS_MESSAGE = 'Incorrect authentication credentials.'
MAX_PER_PAGE = 500


def lookup_credentials(access_key_id):
    """Raises a HawkFail if the passed ID is not equal to
    settings.HAWK_INCOMING_ACCESS_KEY
    """
    if not constant_time_compare(
        access_key_id,
        settings.HAWK_INCOMING_ACCESS_KEY,
    ):
        raise HawkFail('No Hawk ID of {access_key_id}'.format(
            access_key_id=access_key_id,
        ))

    return {
        'id': settings.HAWK_INCOMING_ACCESS_KEY,
        'key': settings.HAWK_INCOMING_SECRET_KEY,
        'algorithm': 'sha256',
    }


def seen_nonce(access_key_id, nonce, _):
    """Returns if the passed access_key_id/nonce combination has been
    used within 60 seconds
    """
    cache_key = 'activity_stream:{access_key_id}:{nonce}'.format(
        access_key_id=access_key_id,
        nonce=nonce,
    )

    # cache.add only adds key if it isn't present
    seen_cache_key = not cache.add(
        cache_key, True, timeout=60,
    )

    if seen_cache_key:
        logger.warning('Already seen nonce {nonce}'.format(nonce=nonce))

    return seen_cache_key


def authorise(request):
    """Raises a HawkFail if the passed request cannot be authenticated"""
    return Receiver(
        lookup_credentials,
        request.META['HTTP_AUTHORIZATION'],
        request.build_absolute_uri(),
        request.method,
        content=request.body,
        content_type=request.content_type,
        seen_nonce=seen_nonce,
    )


class HawkAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        """This is returned as the WWW-Authenticate header when
        AuthenticationFailed is raised. DRF also requires this
        to send a 401 (as opposed to 403)
        """
        return 'Hawk'

    def authenticate(self, request):
        """Authenticates a request using Hawk signature
        If either of these suggest we cannot authenticate, AuthenticationFailed
        is raised, as required in the DRF authentication flow
        """

        return self.authenticate_by_hawk(request)

    def authenticate_by_hawk(self, request):
        if 'HTTP_AUTHORIZATION' not in request.META:
            raise AuthenticationFailed(NO_CREDENTIALS_MESSAGE)

        try:
            hawk_receiver = authorise(request)
        except HawkFail as e:
            logger.warning('Failed authentication {e}'.format(
                e=e,
            ))
            raise AuthenticationFailed(INCORRECT_CREDENTIALS_MESSAGE)

        return (None, hawk_receiver)


class HawkResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response['Server-Authorization'] = request.auth.respond(
            content=response.content,
            content_type=response['Content-Type'],
        )
        return response
