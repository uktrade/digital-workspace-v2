from wagtail.admin.forms import WagtailAdminPageForm

from peoplefinder.models import TeamMember
from peoplefinder.services.person import get_roles


class BasePageForm(WagtailAdminPageForm):
    """
    Override the default Wagtail edit form to remove the inefficient `TeamMember`
    DB call.

    We use JS to supply the functionality, so the initial `page_author_role`
    select options can be empty.

    See: content/static/admin/page_author.js
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["page_author_role"].queryset = TeamMember.objects.none()
        if page_author := self.data.get("page_author"):
            self.fields["page_author_role"].queryset = get_roles(person_pk=page_author)
