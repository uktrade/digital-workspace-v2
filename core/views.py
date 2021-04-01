from django.conf import settings
from django.shortcuts import redirect, render

from notifications_python_client.notifications import NotificationsAPIClient

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
            # Check for last viewed
            last_viewed = request.COOKIES.get("last_viewed")

            if not last_viewed:
                # TODO - handle error
                pass

            trying_to = form.cleaned_data['trying_to']
            what_went_wrong = form.cleaned_data['what_went_wrong']

            personalisation = {
                "user_name": request.user.get_full_name(),
                "user_email": request.user.email,
                "page_url": last_viewed,
                "trying_to": trying_to,
                "what_went_wrong": what_went_wrong,
            },

            notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
            message_sent = notification_client.send_email_notification(
                email_address=settings.SUPPORT_REQUEST_EMAIL,
                template_id=settings.PAGE_PROBLEM_EMAIL_TEMPLATE_ID,
                personalisation={
                    "user_name": request.user.get_full_name(),
                    "user_email": request.user.email,
                    "page_url": last_viewed,
                    "trying_to": trying_to,
                    "what_went_wrong": what_went_wrong,
                },
            )
    else:
        form = PageProblemFoundForm()

    return render(
        request,
        "core/page_problem_found.html",
        {
            "form": form,
            "message_sent": message_sent
        },
    )
