from core.forms import PageProblemFoundForm
from core.models.settings import PageProblemFormSettings
from core.utils import get_all_feature_flags, get_external_link_settings


def global_context(request):
    section = "main"
    if "working-at-dbt" in request.path:
        section = "working_here"
    if "peoplefinder" in request.path:
        section = "people"
    return {
        "SECTION": section,
        "USER_IS_AUTHENTICATED": request.user.is_authenticated,
        "PAGE_PROBLEM_FORM": PageProblemFoundForm(
            initial={"page_url": request.build_absolute_uri()}
        ),
        "PAGE_PROBLEM_FORM_CONTENT": PageProblemFormSettings.load(
            request_or_site=request
        ),
        "FEATURE_FLAGS": get_all_feature_flags(request),
        "EXTERNAL_LINKS_SETTINGS": get_external_link_settings(request),
    }
