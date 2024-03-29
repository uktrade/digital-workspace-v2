# Generated by Django 3.1.8 on 2021-06-09 15:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0014_auto_20210609_0943"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="fluent_languages",
            field=models.CharField(
                blank=True,
                help_text="Add languages that you are fluent in. Use a comma to separate languages.",
                max_length=100,
                null=True,
                verbose_name="Which languages do you speak fluently?",
            ),
        ),
        migrations.AddField(
            model_name="person",
            name="intermediate_languages",
            field=models.CharField(
                blank=True,
                help_text="Add languages that you speak but aren't fluent in. Use a comma to separate languages.",
                max_length=100,
                null=True,
                verbose_name="Which other languages do you speak?",
            ),
        ),
    ]
