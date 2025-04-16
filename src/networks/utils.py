import inspect
from typing import Tuple, Type

from django.contrib.contenttypes.models import ContentType
from django.db import connections, models, transaction

from networks.models import Network, NetworkContentPage, NetworksHome


# TODO: Remove as part of INTR-517
def find_first_common_ancestor(
    from_model: Type[models.Model],
    to_model: Type[models.Model],
) -> Type[models.Model]:
    if from_model == to_model:
        return from_model

    from_mro = inspect.getmro(from_model)
    to_mro = inspect.getmro(to_model)

    for from_cls in from_mro:
        if from_cls in to_mro and not from_cls._meta.abstract:
            return from_cls

    raise ValueError("No common ancestor found")


# TODO: Remove as part of INTR-517
def get_next_model_from_mro(
    model: Type[models.Model],
) -> Type[models.Model]:
    for cls in inspect.getmro(model):
        if cls == model:
            continue
        if not cls._meta.abstract:
            return cls
    raise ValueError("No concrete class found")


# TODO: Remove as part of INTR-517
def build_values(values: list) -> list[str]:
    output_values = []

    for v in values:
        if isinstance(v, bool):
            output_values.append(str(v))
        else:
            output_values.append(f"'{str(v)}'")

    return output_values


# TODO: Remove as part of INTR-517
@transaction.atomic
def convert(
    model_instance: models.Model,
    to_model: Type[models.Model],
    default_data: dict | None = None,
):
    db_connection = connections["default"]

    if default_data is None:
        default_data = {}

    common_ancestor = find_first_common_ancestor(model_instance.__class__, to_model)

    # Clear all tables up to the common ancestor
    for cls in inspect.getmro(model_instance.__class__):
        if cls == common_ancestor:
            break
        if cls._meta.abstract:
            continue
        next_mro_class = get_next_model_from_mro(cls)
        ptr_field_name = f"{next_mro_class._meta.model_name}_ptr_id"
        # Clear the row from the `networks_network` table
        with db_connection.cursor() as cursor:
            cursor.execute(
                f"""
                DELETE FROM {cls._meta.db_table}
                WHERE {ptr_field_name}={f"'{model_instance.pk}'"};
                """,  # noqa: S608
            )

    # Create all of the tables down to the target model
    to_model_mro = inspect.getmro(to_model)
    # Remove everything in the MRO after, and including, the common ancestor
    to_model_mro = to_model_mro[: to_model_mro.index(common_ancestor)]
    # Reverse the MRO so we create the tables in the correct order
    to_model_mro = to_model_mro[::-1]

    # Update the `content_type` value
    if hasattr(common_ancestor, "content_type"):
        common_ancestor_instance = common_ancestor.objects.get(pk=model_instance.pk)
        common_ancestor_instance.content_type = ContentType.objects.get_for_model(
            to_model
        )
        common_ancestor_instance.save(update_fields=["content_type_id"])

    previous_mro_class = common_ancestor
    for cls in to_model_mro:
        # Skip abstract classes
        if cls._meta.abstract:
            continue

        new_cls_fields = [f.name for f in cls._meta.get_fields()]
        new_cls_kwargs = model_instance.__dict__.copy()

        # Get a list of fields that are not in the new class
        fields_to_remove = set(new_cls_kwargs.keys()) - set(new_cls_fields)
        # Clear the base Model fields.
        if issubclass(cls, common_ancestor):
            fields_to_remove.update(
                set(
                    [
                        f.name
                        for f in common_ancestor._meta.get_fields()
                        if f.name in new_cls_kwargs
                    ]
                )
            )

        for field in fields_to_remove:
            del new_cls_kwargs[field]

        new_cls_kwargs[f"{previous_mro_class._meta.model_name}_ptr_id"] = (
            model_instance.id
        )

        if cls in default_data:
            new_cls_kwargs.update(default_data[cls])

        # Add the row to the new table.
        with db_connection.cursor() as cursor:
            table_name = cls._meta.db_table
            fields = ",".join(new_cls_kwargs.keys())
            values = ",".join([v for v in build_values(new_cls_kwargs.values())])
            cursor.execute(
                f"""
                INSERT INTO {table_name} ({fields})
                VALUES ({values});
                """  # noqa: S608
            )

        previous_mro_class = cls

        if cls == to_model:
            break


# TODO: Remove as part of INTR-517
def convert_network_to_content_page(page: Network):
    """
    Convert a network page to a content page.
    """
    convert(
        model_instance=page,
        to_model=NetworkContentPage,
        default_data={
            NetworkContentPage: {
                "content_owner_id": page.content_owner_id,
                "content_contact_email": page.content_contact_email,
            }
        },
    )


# TODO: Remove as part of INTR-517
def convert_network_content_page_to_network(page: NetworkContentPage):
    """
    Convert a network page to a content page.
    """
    convert(
        model_instance=page,
        to_model=Network,
        default_data={
            Network: {
                "content_owner_id": page.content_owner_id,
                "content_contact_email": page.content_contact_email,
            }
        },
    )


# TODO: Remove as part of INTR-517
def convert_network_to_networks_home(page: Network):
    """
    Convert a network page to a networks home page.
    """
    convert(model_instance=page, to_model=NetworksHome)


def get_active_network_types() -> list[Tuple[str]]:
    network_types = (
        Network.objects.live()
        .public()
        .exclude(network_type__isnull=True)
        .values_list("network_type", flat=True)
        .distinct()
    )
    return [
        (nt.value, nt.label) for nt in Network.NetworkTypes if nt.value in network_types
    ]
