from tools.models import IrapToolData, IrapToolDataImport


def diff_irap_data(old: IrapToolData, new: IrapToolDataImport) -> tuple[[], bool]:
    fields = new._meta.get_fields()
    changed = False
    changes = []
    # TO DO safety checks that the two records have the same pk
    for field in fields:
        new_value = getattr(IrapToolDataImport, field.name)
        old_value = getattr(IrapToolData, field.name)
        if old_value != new_value:
            changed = True
            setattr(new, field.name, new_value)
            changes.append(
                {
                    "action": "change",
                    "key": field.name,
                    "from_value": old_value,
                    "to_value": new_value,
                }
            )
        return changed, changes


def process_import():
    """To be called after the irap data has been imported successfully from DW"""
    # Clear all the relevant statuses on target table
    # Set the status to deleted: each record in the import table
    # is checked against the records in the irap table and the status is
    # set accordingly. So if the records does not exist in the import table
    # it has been deleted
    # Set reviewed to False: it will be set to True when the administrator
    # addresses the NEW, CHANGED and DELETED status
    IrapToolData.objects.update(
        after_import_status=IrapToolData.AfterImportStatus.DELETED,
        processed=False,
        changed_fields=None,
    )

    imported_iraps = IrapToolDataImport.objects.all()
    for imported_irap in imported_iraps:
        irap, created = IrapToolData.objects.get_or_create(
            product_irap_reference_number=imported_irap.product_irap_reference_number
        )
        if created:
            irap.product_name = imported_irap.product_name
            irap.functionality = imported_irap.functionality
            irap.AfterImportStatus = IrapToolData.AfterImportStatus.NEW
        else:
            changed, changes = diff_irap_data(imported_irap, irap)
            if changed:
                irap.AfterImportStatus = IrapToolData.AfterImportStatus.CHANGED
                irap.changed_fields = changes
            else:
                irap.AfterImportStatus = IrapToolData.AfterImportStatus.UNCHANGED
                irap.reviewed = True
        irap.save()
