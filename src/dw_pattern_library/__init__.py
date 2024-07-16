# The purpose of this package is to provide overrides and permissions for the
# Django Pattern Library.

# If we stop using the Django Pattern Library, we can remove the following:
# - dw_pattern_library/middleware.py::PatternLibraryAccessMiddleware
# - dw_pattern_library/models.py::PatternLibrary
# - dw_pattern_library/templates/pattern-library-base.html
# - dw_pattern_library/templatetags

# We should also create a migration to delete the PatternLibrary model, run that
# migration on production. Only after this has been done will it be ok to delete
# this package.
