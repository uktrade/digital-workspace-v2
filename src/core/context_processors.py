from core.forms import PageProblemFoundForm
from core.utils import get_all_feature_flags, get_external_link_settings


def global_context(request):
    return {
        "USER_IS_AUTHENTICATED": request.user.is_authenticated,
        "PAGE_PROBLEM_FORM": PageProblemFoundForm(
            initial={"page_url": request.build_absolute_uri()}
        ),
        "FEATURE_FLAGS": get_all_feature_flags(request),
        "EXTERNAL_LINKS_SETTINGS": get_external_link_settings(request),
    }
