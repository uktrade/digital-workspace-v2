# -*- coding: utf-8 -*-
from django.db import migrations


def create_homepage(apps, schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    Page = apps.get_model('wagtailcore.Page')
    Site = apps.get_model('wagtailcore.Site')
    HomePage = apps.get_model('home.HomePage')

    Page.objects.filter(slug="home").delete()

    # Create content type for homepage model
    homepage_content_type, _ = ContentType.objects.get_or_create(
        model='homepage',
        app_label='home',
    )

    # Create a new homepage
    homepage = HomePage.objects.create(
        title="Home",
        draft_title="Home",
        slug='home',
        content_type=homepage_content_type,
        path='00010001',
        depth=2,  # Parents to root
        numchild=0,
        url_path='/home/',
    )

    # Create a site with the new homepage set as the root
    Site.objects.create(
        hostname='localhost',
        root_page=homepage,
        is_default_site=True,
    )


def remove_homepage(apps, schema_editor):
    # Get models
    ContentType = apps.get_model('contenttypes.ContentType')
    Page = apps.get_model('wagtailcore.Page')

    # Delete the default homepage
    # Page and Site objects CASCADE
    Page.objects.filter(slug="home").delete()

    # Delete content type for homepage model
    ContentType.objects.filter(model='homepage', app_label='home').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_homepage,
            remove_homepage,
        ),
    ]
