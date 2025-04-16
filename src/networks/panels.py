from core import flags
from core.panels import FieldPanel


class NetworkTypesFlaggedFieldPanel(FieldPanel):
    class BoundPanel(FieldPanel.BoundPanel):
        template_name = "networks/panels/network_types_flagged_field_panel.html"

        def get_context_data(self, parent_context=None):
            from waffle import flag_is_active

            context = super().get_context_data(parent_context=parent_context)
            context["flag_is_active"] = flag_is_active(
                self.request, flags.NETWORK_TYPES
            )
            return context
