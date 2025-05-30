# Generated by Django 5.1.7 on 2025-03-24 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0020_comment_edited_date_historicalcomment_edited_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newspage",
            name="perm_sec_as_author",
            field=models.BooleanField(
                default=False,
                help_text="To set the author of a page, go to the 'Publishing' tab and select a 'Page author'",
            ),
        ),
    ]
