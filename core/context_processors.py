from core.forms import PageProblemFoundForm


def page_problem_form(request):
    return {
        "PAGE_PROBLEM_FORM": PageProblemFoundForm(
            initial={"page_url": request.build_absolute_uri()}
        )
    }
