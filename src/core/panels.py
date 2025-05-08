from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    PageChooserPanel,
)

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
            if self.bound_field and not self.bound_field.field.required:
                self.heading += " (optional)"


class InlinePanel(InlinePanel):
    class BoundPanel(InlinePanel.BoundPanel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.panel.min_num is None or self.panel.min_num == 0:
                self.heading += " (optional)"
