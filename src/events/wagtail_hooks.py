from django.templatetags.static import static
from django.utils.safestring import mark_safe
from wagtail import hooks


@hooks.register("insert_editor_js")
def editor_js():
    events_admin_js_path = static("admin/events.js")
    return mark_safe(  # noqa: S308
        f"<script src='{events_admin_js_path}'></script>"
    )
