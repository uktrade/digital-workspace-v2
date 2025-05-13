from django.utils.functional import cached_property
from wagtail import blocks

from content.utils import team_members


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


class PageAuthorBlock(blocks.StructBlock):
    # page_author = blocks.CharBlock()

    # quote_theme = blocks.ChoiceBlock(
    #     choices=[("light", "Light"), ("dark", "Dark")],
    #     default="true",
    #     help_text="Colour of the background. This can either be light grey or dark blue",
    # )
    page_author = PersonChooserBlock(required=False)
    # source_name = blocks.CharBlock(required=False)
    page_author_role_id = blocks.ChoiceBlock(
        choices=team_members,
        required=False,
        label="Page author role",
        help_text="Choose the person's job role. If you do not want to show a job role, choose 'Hide role'.",
    )
    page_author_role = blocks.CharBlock(required=False, label="Page author role")
    page_author_team = blocks.CharBlock(required=False, label="Page author team")
    # source_image = ImageChooserBlock(
    #     required=False, help_text="This image should be square"
    # )

    class Meta:
        # template = "dwds/components/quote.html"
        icon = "person"
        label = "Page Author"

    def clean(self, value):
        # if value["page_author"] and (
        #     value["source_name"]
        #     or value["source_role"]
        #     or value["source_team"]
        #     or value["source_image"]
        # ):
        #     raise ValidationError(
        #         "Either choose a source or enter the details manually."
        #     )
        return super().clean(value)

    # def get_context(self, value, parent_context=None):
    #     context = super().get_context(value, parent_context)
    #     # context.update(page_author=value["page_author"], highlight=True)
    #     context.update(page_author=value["page_author"])
    #     # if value["quote_theme"] == "light":
    #     #     context.update(highlight=False)
    #     if page_author := value["page_author"]:
    #         context.update(
    #             page_author_name=value["page_author"].full_name,
    #             page_author_url=value["page_author"].get_absolute_url(),
    #             page_author_image_url=(
    #                 value["page_author"].photo.url if value["page_author"].photo else None
    #             ),
    #         )
    #         if page_author_role := page_author.roles.first():
    #             context.update(
    #                 page_author_role=page_author_role.job_title,
    #                 page_author_team_name=page_author_role.team.name,
    #                 page_author_team_url=page_author_role.team.get_absolute_url(),
    #             )
    #     else:
    #         context.update(
    #             page_author_name=value["page_author_name"],
    #             page_author_role=value["page_author_role"],
    #             page_author_team_name=value["page_author_team"],
    #             page_author_image=value["page_author_image"],
    #         )
    #     return context
