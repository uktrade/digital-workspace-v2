# Generated by Django 3.2.17 on 2023-02-09 14:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0012_auto_20220110_1506"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="historicalcomment",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical comment",
                "verbose_name_plural": "historical comments",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalnewscategory",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical news category",
                "verbose_name_plural": "historical Categories",
            },
        ),
        migrations.AlterField(
            model_name="historicalcomment",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalnewscategory",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
    ]
