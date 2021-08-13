from core.admin import admin_site
from simple_history.admin import SimpleHistoryAdmin
from wagtail.documents.models import Document


class DocumentAdmin(SimpleHistoryAdmin):
    list_display = ["title", "created_at", "uploaded_by_user"]

    search_fields = [
        'title',
        'created_at',
        'uploaded_by_user__first_name',
        'uploaded_by_user__last_name',
        'uploaded_by_user__email',
    ]


admin_site.register(Document, DocumentAdmin)
