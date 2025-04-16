from django.conf import settings


def dev_tools(request):
    return {
        "DEV_TOOLS_ENABLED": settings.DEV_TOOLS_ENABLED,
    }
