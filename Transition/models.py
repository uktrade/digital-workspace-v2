from content.models import ContentPage


class Transition(ContentPage):
    is_creatable = True

    parent_page_types = ['transition.TransitionHome']
    subpage_types = ["transition.Transition", ]


class TransitionHome(ContentPage):
    is_creatable = False

    subpage_types = ["transition.Transition", ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        children = Transition.objects.all().order_by("title")

        context["children"] = children

        return context