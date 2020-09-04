from content.models import ContentPage, DirectChildrenMixin


class Transition(DirectChildrenMixin, ContentPage):
    is_creatable = True

    parent_page_types = ['transition.TransitionHome']
    subpage_types = ["transition.Transition", ]


class TransitionHome(DirectChildrenMixin, ContentPage):
    is_creatable = False

    subpage_types = ["transition.Transition", ]
