from content.models import ContentPage


class TransitionHome(ContentPage):
    is_creatable = False

    subpage_types = ["transition.Transition", ]


class Transition(ContentPage):
    is_creatable = True

    parent_page_types = ['transition.TransitionHome']
    subpage_types = ["transition.Transition", ]
