from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0121_merge_20240430_0948"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="ical_token",
            field=models.CharField(
                blank=True,
                max_length=80,
                null=True,
                verbose_name="Individual token for iCal feeds",
            ),
        ),
    ]
