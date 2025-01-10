import inspect
from typing import Type

from django.contrib.contenttypes.models import ContentType
from django.db import connections, transaction
from wagtail.models import Page

from networks.models import Network, NetworkContentPage, NetworksHome


def page_conversion_compatible(
    from_page_type: Type[Page], to_page_type: Type[Page], allow_one_way: bool = False
) -> bool:
    """
    Check if a page can be converted to another page type.

    If `allow_one_way` is True, then the conversion is allowed if the MRO of the
    "to" page type is a subset of the MRO of the "from" page type. This means
    that data might be lost in the conversion.
    """
    # Check that the MROs are compatible (skip the first element as it is the
    # page type itself)
    from_page_mro = inspect.getmro(from_page_type)[1:]
    to_page_mro = inspect.getmro(to_page_type)[1:]

    if allow_one_way:
        return set(to_page_mro).issubset(set(from_page_mro))
    return from_page_mro == to_page_mro


@transaction.atomic
def convert_page(
    page: Page, page_type: Type[Page], allow_one_way: bool = False
) -> NetworkContentPage:
    """
    Convert a page to a given page type.
    """
    page = page.specific

    if not page_conversion_compatible(
        from_page_type=page.__class__,
        to_page_type=page_type,
        allow_one_way=allow_one_way,
    ):
        raise ValueError(
            f"Page type {page.__class__} cannot be converted to {page_type}"
        )

    db_connection = connections["default"]

    new_content_fields: list[str] = []
    # Get content type specific fields from the table.
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s;
            """,
            [page_type._meta.db_table],
        )
        for row in cursor.fetchall():
            new_content_fields.append(row[0])

    print(new_content_fields)

    # Add the row to the new table.
    with db_connection.cursor() as cursor:
        table_name = page_type._meta.db_table
        fields = ",".join(new_content_fields)
        values = ",".join(
            [f"'{str(getattr(page, field))}'" for field in new_content_fields]
        )
        cursor.execute(
            f"""
            INSERT INTO {table_name} ({fields})
            VALUES ({values});
            """
        )

    # Get the content type
    app_label = page_type._meta.app_label
    model_name = page_type._meta.model_name
    content_type = ContentType.objects.get(app_label=app_label, model=model_name)

    # Update the `wagtailcore_page` table to change the `content_type_id`
    wagtail_page = Page.objects.get(pk=page.pk)
    wagtail_page.content_type = content_type
    wagtail_page.save(update_fields=["content_type_id"])

    # Clear the row from the `networks_network` table
    with db_connection.cursor() as cursor:
        cursor.execute(
            f"""
            DELETE FROM {page.__class__._meta.db_table} WHERE contentpage_ptr_id=%s;
            """,
            [str(page.contentpage_ptr_id)],
        )


def convert_network_to_content_page(page: Network):
    """
    Convert a network page to a content page.
    """
    convert_page(page=page, page_type=NetworkContentPage)


def convert_network_content_page_to_network(page: NetworkContentPage):
    """
    Convert a network page to a content page.
    """
    convert_page(page=page, page_type=Network)


def convert_network_to_networks_home(page: Network):
    """
    Convert a network page to a networks home page.
    """
    convert_page(page=page, page_type=NetworksHome, allow_one_way=True)
