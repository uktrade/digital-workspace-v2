# Generated by Django 4.1.10 on 2023-10-25 09:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0118_alter_person_email"),
        ("networks", "0003_remove_network_excerpt"),
    ]

    operations = [
        migrations.AddField(
            model_name="network",
            name="content_contact_email",
            field=models.EmailField(
                help_text="Contact email shown on article, this could be the content owner or a team inbox",
                max_length=254,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="network",
            name="content_owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="peoplefinder.person",
            ),
        ),
    ]
