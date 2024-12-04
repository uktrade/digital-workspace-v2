from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel

from core.widgets import ReadOnlyPageInput


class PageSelectorPanel(PageChooserPanel):
    class BoundPanel(PageChooserPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            if self.instance and self.instance.pk:
                self.bound_field.field.widget = ReadOnlyPageInput()

class FieldPanel(FieldPanel):
    class BoundPanel(FieldPanel.BoundPanel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if not self.bound_field.field.required:
                self.heading += " (optional)"

class InlinePanel(InlinePanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.min_num is None or self.min_num == 0:
            if not self.heading.endswith(" (optional)"):
                self.heading += " (optional)"
