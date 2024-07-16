from django.core.exceptions import PermissionDenied
from django.urls import resolve
from pattern_library.urls import app_name


class PatternLibraryAccessMiddleware:
    """
    Prevent access to the pattern library to only users with permission

    This middleware can be removed if we move away from Django Pattern Library.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip if the current URL does not belong to the pattern library
        resolved_request = resolve(request.path)
        if resolved_request.app_name != app_name:
            return self.get_response(request)

        # Allow if the user has permission to access the pattern library
        if request.user.has_perm("dw_pattern_library.view_dpl"):
            return self.get_response(request)

        # Return a 403 Forbidden response if the user does not have permission
        raise PermissionDenied(
            "You do not have permission to access the pattern library."
        )
