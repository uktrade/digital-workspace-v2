from django.shortcuts import redirect


def view_404(request, exception):
    return redirect("/404/")


def view_500(request):
    return redirect("/500/")


def view_403(request, exception):
    return redirect("/403/")


def view_400(request, exception):
    return redirect("/400/")
