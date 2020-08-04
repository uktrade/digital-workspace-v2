# -*- coding: utf-8 -*-
from django.db import migrations
from wagtail.core.models import Page

def create_homepage(apps, schema_editor):
    # Get models
    ContentType = apps.get_model('contenttypes.ContentType')
    TopicHomePage = apps.get_model('content.TopicHomePage')



    home_page = Page.objects.filter(slug="home").first()

    # Create content type for homepage model
    topic_homepage_content_type, __ = ContentType.objects.get_or_create(
        model='topichomepage', app_label='content')

    # Create a new homepage
    topic_home_page = TopicHomePage.objects.create(
        title="Topics Home",
        draft_title="Topics Home",
        slug='topics_home',
        content_type=topic_homepage_content_type,
        path='00010002',
        depth=3,
        numchild=0,
        url_path='/topics/',
    )

    #home_page.add_child(instance=topic_home_page)
    #home_page.save()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_create_homepage'),
        ('content', '0007_topichomepage_topicpage'),
    ]

    operations = [
        migrations.RunPython(create_homepage),
    ]
