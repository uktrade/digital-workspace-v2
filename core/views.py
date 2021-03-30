from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from core.forms import PageProblemFoundForm


def view_404(request, exception):
    return redirect("/404/")


def view_500(request):
    return redirect("/500/")


def view_403(request, exception):
    return redirect("/403/")


def view_400(request, exception):
    return redirect("/400/")


def page_problem_found(request):
    message_sent = False

    if request.method == 'POST':
        form = PageProblemFoundForm(request.POST)
        if form.is_valid():
            trying_to = form.cleaned_data['trying_to']
            what_went_wrong = form.cleaned_data['what_went_wrong']

            subject = "Digital Workspace page problem form submitted"
            message = f"<b>What were you trying to do?</b><p>{trying_to}</p>"
            message += f"<b>What went wrong?</b><p>{what_went_wrong}</p>"

            message_sent = send_mail(
                subject,
                message,
                request.user.email,
                settings.SUPPORT_REQUEST_EMAILS,
            )
    else:
        form = PageProblemFoundForm()

    return render(
        request,
        "page_problem_found.html",
        {
            "form": form,
            "message_sent": message_sent
        },
    )
