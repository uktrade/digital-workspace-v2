import logging

from django.conf import settings
from django.shortcuts import render
from notifications_python_client.notifications import NotificationsAPIClient

from core.forms import PageProblemFoundForm


logger = logging.getLogger(__name__)


def view_404(request, exception):
    return render(
        request,
        "core/404.html",
        {"page_problem_form": PageProblemFoundForm()},
        status=404,
    )


def view_500(request):
    return render(
        request,
        "core/500.html",
        {"page_problem_form": PageProblemFoundForm()},
        status=500,
    )


def view_403(request, exception):
    return render(
        request,
        "core/403.html",
        {"page_problem_form": PageProblemFoundForm()},
        status=403,
    )


def view_400(request, exception):
    return render(
        request,
        "core/400.html",
        {"page_problem_form": PageProblemFoundForm()},
        status=403,
    )


def page_problem_found(request):
    message_sent = False

    if request.method == "POST":
        form = PageProblemFoundForm(request.POST)

        if form.is_valid():
            page_url = form.cleaned_data["page_url"]
            trying_to = form.cleaned_data["trying_to"]
            what_went_wrong = form.cleaned_data["what_went_wrong"]

            notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
            message_sent = notification_client.send_email_notification(
                email_address=settings.SUPPORT_REQUEST_EMAIL,
                template_id=settings.PAGE_PROBLEM_EMAIL_TEMPLATE_ID,
                personalisation={
                    "user_name": request.user.get_full_name(),
                    "user_email": request.user.email,
                    "page_url": page_url,
                    "trying_to": trying_to,
                    "what_went_wrong": what_went_wrong,
                },
            )
    else:
        form = PageProblemFoundForm()

    return render(
        request,
        "core/page_problem_found.html",
        {"form": form, "message_sent": message_sent},
    )
