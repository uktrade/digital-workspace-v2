from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)
from wagtail.fields import RichTextField

from core.panels import FieldPanel


@register_setting
class PageProblemFormSettings(BaseGenericSetting):
    content = RichTextField()

    panels = [FieldPanel("content")]
