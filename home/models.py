from django.db import models
from django.core.exceptions import ValidationError

from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.admin.edit_handlers import (
    FieldPanel,
    PageChooserPanel,
)
from wagtail.snippets.models import register_snippet

from modelcluster.fields import ParentalKey
from wagtail.core.models import Page


@register_snippet
class QuickLink(models.Model):
    title = models.CharField(max_length=255)
    link_to = ParentalKey(
        'content.ContentPage',
        on_delete=models.CASCADE,
        related_name='quick_links_pages',
    )

    def __str__(self):
        return f"'{self.title}' which links to the '{self.link_to.title}' page"

    panels = [
        FieldPanel('title'),
        PageChooserPanel('link_to'),
    ]

    class Meta:
        ordering = ['-title']


@register_snippet
class WhatsPopular(models.Model):
    title = models.CharField(max_length=255)
    link_to = ParentalKey(
        'content.ContentPage',
        on_delete=models.CASCADE,
        related_name='whats_popular_pages',
        blank=True,
        null=True,
    )
    external_url = models.URLField(
        blank=True,
        null=True,
    )
    preview_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    def __str__(self):
        return self.title

    panels = [
        FieldPanel('title'),
        ImageChooserPanel("preview_image"),
        PageChooserPanel('link_to'),
        FieldPanel('external_url'),
    ]

    class Meta:
        ordering = ['-title']

    def clean(self):
        if self.external_url and self.link_to:
            raise ValidationError(
                "Please choose an external URL or a page within the site. "
                "You cannot have both."
            )

        page_count = WhatsPopular.objects.count()

        if page_count > 2:
            raise ValidationError(
                "You can have a maximum of 3 \"what's popular\" pages. "
                "Please remove one of the others before adding a new one."
            )


@register_snippet
class HowDoIPreview(models.Model):
    how_do_i_page = ParentalKey(
        'working_at_dit.HowDoI',
        on_delete=models.CASCADE,
        related_name='how_do_i_on_home_pages',
    )

    def __str__(self):
        return self.how_do_i_page

    panels = [
        PageChooserPanel('how_do_i_page'),
    ]


class HomePage(Page):
    is_creatable = False
    show_in_menus = True

    subpage_types = []

    def get_context(self, request, *args, **kwargs):
        context = super(HomePage, self).get_context(request, *args, **kwargs)
        #context['posts'] = self.posts
        #context['blog_page'] = self

        context['menu_items'] = self.get_children().filter(
            live=True,
            show_in_menus=True,
        )

        return context
