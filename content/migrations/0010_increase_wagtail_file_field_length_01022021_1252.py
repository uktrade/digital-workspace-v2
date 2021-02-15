from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0009_auto_20210127_0947"),
        ("wagtailimages", "__latest__"),
        ("wagtailmedia", "__latest__"),
        ("wagtaildocs", "__latest__"),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE public.wagtailimages_image ALTER COLUMN file TYPE varchar(500);"
            "ALTER TABLE public.wagtaildocs_document ALTER COLUMN file TYPE varchar(500);"
            "ALTER TABLE public.wagtailmedia_media ALTER COLUMN file TYPE varchar(500);"
        )
    ]
