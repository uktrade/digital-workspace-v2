from core.admin import admin_site
from simple_history.admin import SimpleHistoryAdmin
from wagtail.documents.models import Document


class DocumentAdmin(SimpleHistoryAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    # make everything read only for non-super users
    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            self.readonly_fields = [
                field.name for field in obj.__class__._meta.fields
            ]
        return self.readonly_fields

    list_display = ["title", "created_at", "uploaded_by_user"]

    search_fields = [
        'title',
        'created_at',
        'uploaded_by_user__first_name',
        'uploaded_by_user__last_name',
        'uploaded_by_user__email',
    ]


admin_site.register(Document, DocumentAdmin)
