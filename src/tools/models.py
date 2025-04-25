from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.shortcuts import redirect

from content.models import ContentPage
from core import field_models
from core.models import fields
from core.panels import FieldPanel
from extended_search.index import DWIndexedField as IndexedField
from working_at_dit.models import PageWithTopics


class IrapToolDataAbstract(models.Model):
    # This abstract class matches the data imported from Data workspace
    product_irap_reference_number = models.IntegerField(primary_key=True)
    product_name = field_models.CharField(
        max_length=2048,
        null=True,
        blank=True,
    )
    functionality = field_models.CharField(
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
    # The data from Data Workspace are copied here,and after are
    # validated are copied to the tool models.
    # If something goes wrong during the import,
    # the import will be aborted, and the tool data will still be correct
    pass


class IrapToolData(IrapToolDataAbstract):
    # UNDELETED is used for flagging an irap record that:
    # was present in import 1
    # was not present in import 2
    # was present in import 3
    # was not reviewed after import 2
    # very unlikely situation
    class AfterImportStatus(models.TextChoices):
        NEW = "new", "new"
        CHANGED = "changed", "Changed"
        DELETED = "deleted", "Deleted"
        UNDELETED = "undeleted", "Undeleted"
        REVIEWED = "reviewed", "Reviewed"

    after_import_status = field_models.CharField(
        max_length=9, choices=AfterImportStatus.choices, default=AfterImportStatus.NEW
    )
    review_date = models.DateTimeField(null=True, blank=True)

    imported = models.BooleanField(default=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    previous_fields = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)

    def __str__(self):
        return self.product_name


class Tool(PageWithTopics):
    template = "content/content_page.html"
    is_creatable = True
    irap_tool = models.OneToOneField(
        IrapToolData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    redirect_url = fields.URLField(
        null=True,
        blank=True,
    )
    long_description = field_models.CharField(
        null=True,
        blank=True,
        max_length=2048,
    )

    indexed_fields = [
        IndexedField(
            "search_tool_name",
            fuzzy=True,
            tokenized=True,
            explicit=True,
            autocomplete=True,
            keyword=True,
            boost=10.0,
        ),
    ]

    @property
    def search_tool_name(self):
        return self.title

    parent_page_types = ["tools.ToolsHome"]
    subpage_types = []  # Should not be able to create children

    content_panels = PageWithTopics.content_panels + [
        FieldPanel("redirect_url"),
        FieldPanel(
            "irap_tool",
            widget=forms.TextInput(attrs={"disabled": "true"}),
        ),
    ]

    def serve(self, request):
        return redirect(self.redirect_url)


class ToolsHome(ContentPage):
    is_creatable = False
    subpage_types = ["tools.Tool"]
    template = "content/content_page.html"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["children"] = Tool.objects.live().public().order_by("title")
        context["num_cols"] = 3
        context["target_blank"] = True

        return context
