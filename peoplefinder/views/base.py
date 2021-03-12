from django.conf import settings
from django.shortcuts import redirect
from django.views import View


class PeoplefinderView(View):
    def dispatch(self, request, *args, **kwargs):
        if not settings.PEOPLEFINDER_V2:
            return redirect(settings.PEOPLEFINDER_URL + request.path)

        return super().dispatch(request, *args, **kwargs)
