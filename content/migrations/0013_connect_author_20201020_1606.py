# -*- coding: utf-8 -*-
from django.db import migrations

from django.contrib.auth import get_user_model

UserModel = get_user_model()


def create_connect_author(apps, schema_editor):
    connect_author = UserModel(email="connect@digital.trade.gov.uk")
    connect_author.save()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0012_contentpage_search_title'),
    ]

    operations = [
        migrations.RunPython(
            create_connect_author,
            migrations.RunPython.noop,
        ),
    ]
