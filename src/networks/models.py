from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import EmptyPage, Paginator
from django.db import models
from wagtail.models import Page

import peoplefinder.models as pf_models
from content.forms import BasePageForm
from content.models import ContentOwnerMixin, ContentPage
from core.panels import FieldPanel, PageChooserPanel
from extended_search.index import DWIndexedField as IndexedField


class NetworksHome(ContentPage):
    is_creatable = False
    subpage_types = ["networks.Network", "networks.NetworkContentPage"]
    template = "networks/networks_home.html"

    promote_panels = ContentPage.promote_panels + [
        FieldPanel("useful_links"),
        PageChooserPanel("spotlight_page"),
    ]

    def get_context(self, request, *args, **kwargs):
        from networks.filters import NetworksFilters

        context = super().get_context(request, *args, **kwargs)

        # Filtering networks by network type
        networks_filters = NetworksFilters(
            request.GET,
            queryset=Network.objects.live().public().order_by("title"),
        )
        networks = networks_filters.qs

        paginator = Paginator(networks, 15)
        page = int(request.GET.get("page", 1))

        try:
            networks = paginator.page(page)
        except EmptyPage:
            networks = paginator.page(paginator.num_pages)

        context["networks_filters"] = networks_filters
        context["networks"] = networks

        context["attribution"] = False
        context["num_cols"] = 3

        return context


def peoplefinder_network_choices():
    yield (None, "------")

    for network in pf_models.Network.objects.all():
        yield (network.pk, str(network))


class NetworkForm(BasePageForm):
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
        elif not page._state.adding:
            pf_models.NewNetwork.objects.filter(page=page).delete()

        if commit:
            page.save()

        return page


class Network(ContentOwnerMixin, ContentPage):
    is_creatable = True

    parent_page_types = [
        "networks.NetworksHome",
        "networks.Network",
        "networks.NetworkContentPage",
    ]

    template = "content/content_page.html"
    subpage_types = ["networks.Network", "networks.NetworkContentPage"]

    class NetworkTypes(models.TextChoices):
        DBT_INITIATIVES = "dbt_initiatives", "DBT initiatives"
        DEPARTMENT_FUNCTION = "department_function", "Department/function"
        DIVERSITY_AND_INCLUSION = "diversity_and_inclusion", "Diversity and inclusion"
        HEALTH_AND_WELLBEING = "health_and_wellbeing", "Health and wellbeing"
        INTERESTS_AND_HOBBIES = "interests_and_hobbies", "Interests and hobbies"
        PROFESSIONAL_NETWORKS_AND_SKILLS = (
            "professional_networks_and_skills",
            "Professional networks and skills",
        )
        SOCIAL_AND_SPORTS = "social_and_sports", "Social and sports"
        VOLUNTEERING = "volunteering", "Volunteering"

    network_type = models.CharField(
        max_length=50,
        choices=NetworkTypes.choices,
        blank=True,
        null=True,
    )

    content_panels = ContentPage.content_panels + [
        FieldPanel("network_type"),
        FieldPanel("is_peoplefinder_network"),
        FieldPanel("peoplefinder_network"),
    ]

    promote_panels = ContentPage.promote_panels + [
        FieldPanel("useful_links"),
        PageChooserPanel("spotlight_page"),
    ]

    base_form_class = NetworkForm

    indexed_fields = [
        IndexedField(
            "topic_titles",
            tokenized=True,
            explicit=True,
        ),
    ] + ContentOwnerMixin.indexed_fields

    def get_template(self, request, *args, **kwargs):
        if Network.objects.live().public().child_of(self).exists():
            self.template = "networks/group_network.html"
        return super().get_template(request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["children"] = (
            ContentPage.objects.live()
            .public()
            .child_of(self)
            .filter(content_type=ContentType.objects.get_for_model(Network))
            .order_by("title")
        )
        context["attribution"] = True
        context["num_cols"] = 3

        return context

    @property
    def peoplefinder_network(self):
        return getattr(self, "newnetwork", None)


class NetworkContentPage(ContentOwnerMixin, ContentPage):
    is_creatable = True

    parent_page_types = [
        "networks.NetworksHome",
        "networks.Network",
    ]

    template = "content/content_page.html"
    subpage_types = ["networks.Network", "networks.NetworkContentPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["children"] = (
            Page.objects.live().public().child_of(self).order_by("title")
        )
        context["attribution"] = True
        context["num_cols"] = 3

        return context
