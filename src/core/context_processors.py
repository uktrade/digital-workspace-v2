from core.forms import PageProblemFoundForm
from home import FEATURE_HOMEPAGE, FEATURE_HOMEPAGE_AVAILABLE


def global_context(request):
    return {
        "USER_IS_AUTHENTICATED": request.user.is_authenticated,
        "PAGE_PROBLEM_FORM": PageProblemFoundForm(
            initial={"page_url": request.build_absolute_uri()}
        ),
        "FEATURE_HOMEPAGE": FEATURE_HOMEPAGE,
        "FEATURE_HOMEPAGE_AVAILABLE": FEATURE_HOMEPAGE_AVAILABLE,
    }
