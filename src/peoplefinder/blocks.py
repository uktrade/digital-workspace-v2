from django.utils.functional import cached_property
from wagtail import blocks


class PersonChooserBlock(blocks.ChooserBlock):
    @cached_property
    def target_model(self):
        from peoplefinder.models import Person

        return Person

    @cached_property
    def widget(self):
        from peoplefinder.widgets import PersonChooser

        return PersonChooser()

    def render_basic(self, value, context=None):
        if value:
            return value
        else:
            return ""

    class Meta:
        icon = "person"
