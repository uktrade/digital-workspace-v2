from wagtail.admin.forms import WagtailAdminPageForm

from peoplefinder.services.person import get_roles


class BasePageForm(WagtailAdminPageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if page_author := self.data.get("page_author"):
            self.fields["page_author_role"].queryset = get_roles(page_author)
