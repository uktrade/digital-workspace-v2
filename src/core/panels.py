from wagtail.admin.panels import PageChooserPanel

from core.widgets import ReadOnlyPageInput


class PageSelectorPanel(PageChooserPanel):
    class BoundPanel(PageChooserPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            if self.instance.pk:
                self.bound_field.field.widget = ReadOnlyPageInput()
