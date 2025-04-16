from django.core.exceptions import ValidationError
from wagtail.admin.forms import WagtailAdminPageForm


class HomePageForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()

        # Priority pages

        priority_page_layout = self.instance.PriorityPagesLayout(
            cleaned_data["priority_pages_layout"]
        )

        page_count_for_layout = sum(priority_page_layout.to_page_counts())

        # Filter out the forms which have been deleted. I found the approach here
        # https://stackoverflow.com/a/71871397.
        priority_pages_forms = [
            form
            for form in self.formsets["priority_pages"]
            if form not in self.formsets["priority_pages"].deleted_forms
        ]
        priority_pages_count = len(priority_pages_forms)

        if priority_pages_count < page_count_for_layout:
            raise ValidationError(
                "Not enough priority pages selected"
                f" ({priority_pages_count} out of {page_count_for_layout} required)"
            )

        # Promotion banner

        if cleaned_data["promo_enabled"]:
            required_promo_fields = [
                "promo_description",
                "promo_link_url",
                "promo_link_text",
                "promo_image",
            ]
            for field in required_promo_fields:
                if not cleaned_data[field]:
                    self.add_error(field, "This field is required.")

        return cleaned_data
