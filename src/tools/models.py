from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.shortcuts import redirect
from wagtail.admin.panels import FieldPanel

from content.models import ContentPage
from working_at_dit.models import PageWithTopics


class IrapToolDataAbstract(models.Model):
    product_irap_reference_number = models.IntegerField(primary_key=True)
    product_name = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
    )
    functionality = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
    )
    date_due_for_re_accreditation = models.DateField(
        null=True,
        blank=True,
    )

    # TODO Add new fields that will be created later:
    #  description and condition of use
    class Meta:
        abstract = True


class IrapToolDataImport(IrapToolDataAbstract):
    pass


class IrapToolData(IrapToolDataAbstract):
    class AfterImportStatus(models.TextChoices):
        NEW = "new", "new"
        CHANGED = "changed", "Changed"
        DELETED = "deleted", "Deleted"
        UNDELETED = "undeleted", "Undeleted"
        REVIEWED = "reviewed", "Reviewed"

    after_import_status = models.CharField(
        max_length=9, choices=AfterImportStatus.choices, default=AfterImportStatus.NEW
    )
    review_date = models.DateTimeField(null=True, blank=True)

    imported = models.BooleanField(default=True)

    created_date = models.DateTimeField(auto_now_add=True)
    previous_fields = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)

    def __str__(self):
        return self.product_name


class Tool(PageWithTopics):
    is_creatable = True
    irap_tool = models.OneToOneField(
        IrapToolData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    redirect_url = models.CharField(
        null=True,
        blank=True,
        max_length=2048,
    )
    long_description = models.CharField(
        null=True,
        blank=True,
        max_length=2048,
    )

    # TODO Move it to a util file
    readonly_widget = forms.TextInput(attrs={"disabled": "true"})

    parent_page_types = ["tools.ToolsHome"]
    subpage_types = []  # Should not be able to create children

    content_panels = PageWithTopics.content_panels + [
        FieldPanel("redirect_url"),
        FieldPanel("irap_tool", widget=readonly_widget),
    ]

    def serve(self, request):
        return redirect(self.redirect_url)


class ToolsHome(ContentPage):
    is_creatable = False

    subpage_types = ["tools.Tool"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["children"] = Tool.objects.live().public().order_by("title")

        return context
