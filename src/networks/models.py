from django import forms
from wagtail.admin.forms import WagtailAdminPageForm

import peoplefinder.models as pf_models
from content.models import ContentOwnerMixin, ContentPage
from core.panels import FieldPanel
from extended_search.index import DWIndexedField as IndexedField


class NetworksHome(ContentPage):
    is_creatable = False

    subpage_types = ["networks.Network"]

    template = "content/content_page.html"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["children"] = (
            Network.objects.live().public().child_of(self).order_by("title")
        )
        context["attribution"] = False
        context["num_cols"] = 3

        return context


def peoplefinder_network_choices():
    yield (None, "------")

    for network in pf_models.Network.objects.all():
        yield (network.pk, str(network))


class NetworkForm(WagtailAdminPageForm):
    is_peoplefinder_network = forms.BooleanField(
        required=False,
        label="Is a People Finder network",
    )
    peoplefinder_network = forms.ChoiceField(
        required=False,
        choices=peoplefinder_network_choices,
        label="Associated People Finder network",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["is_peoplefinder_network"].initial = bool(
            self.instance.peoplefinder_network
        )
        self.fields["peoplefinder_network"].initial = (
            self.instance.peoplefinder_network
            and getattr(self.instance.peoplefinder_network, "old_network", None)
            and self.instance.peoplefinder_network.old_network.pk
        )

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("is_peoplefinder_network") and cleaned_data.get(
            "peoplefinder_network"
        ):
            cleaned_data["peoplefinder_network"] = None

        if (
            cleaned_data.get("peoplefinder_network")
            and pf_models.NewNetwork.objects.filter(
                old_network_id=cleaned_data.get("peoplefinder_network")
            ).exists()
        ):
            self.add_error(
                "peoplefinder_network",
                "Already associated with another network page",
            )

        return cleaned_data

    def save(self, commit=True):
        page = super().save(commit=False)

        if self.cleaned_data.get("is_peoplefinder_network"):
            network, _ = pf_models.NewNetwork.objects.get_or_create(page=page)
            network.old_network_id = self.cleaned_data.get("peoplefinder_network")
            network.save()
        else:
            pf_models.NewNetwork.objects.filter(page=page).delete()

        if commit:
            page.save()

        return page


class Network(ContentOwnerMixin, ContentPage):
    is_creatable = True

    parent_page_types = [
        "networks.NetworksHome",
        "networks.Network",
    ]

    template = "content/content_page.html"
    subpage_types = ["networks.Network"]

    content_panels = ContentPage.content_panels + [
        FieldPanel("is_peoplefinder_network"),
        FieldPanel("peoplefinder_network"),
    ]
    base_form_class = NetworkForm

    indexed_fields = [
        IndexedField(
            "topic_titles",
            tokenized=True,
            explicit=True,
        ),
    ] + ContentOwnerMixin.indexed_fields

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["children"] = (
            Network.objects.live().public().child_of(self).order_by("title")
        )
        context["attribution"] = True
        context["num_cols"] = 3

        return context

    @property
    def peoplefinder_network(self):
        return getattr(self, "newnetwork", None)
