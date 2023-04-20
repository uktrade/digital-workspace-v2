from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0009_auto_20210127_0947"),
        ("wagtailimages", "0001_squashed_0021"),
        ("wagtailmedia", "0003_copy_media_permissions_to_collections"),
        ("wagtaildocs", "0012_uploadeddocument"),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE public.wagtailimages_image ALTER COLUMN file TYPE varchar(500);"
            "ALTER TABLE public.wagtaildocs_document ALTER COLUMN file TYPE varchar(500);"
            "ALTER TABLE public.wagtailmedia_media ALTER COLUMN file TYPE varchar(500);"
        )
    ]
