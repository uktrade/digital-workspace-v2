from core.forms import PageProblemFoundForm


def page_problem_form(request):
    return {
        "USER_IS_AUTHENTICATED": request.user.is_authenticated,
        "PAGE_PROBLEM_FORM": PageProblemFoundForm(
            initial={"page_url": request.build_absolute_uri()}
        ),
    }
