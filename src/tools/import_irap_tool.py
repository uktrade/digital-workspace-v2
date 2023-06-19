from tools.models import IrapToolData, IrapToolDataImport, Tool


def diff_irap_data(old: IrapToolData, new: IrapToolDataImport) -> tuple[[], bool]:
    fields = new._meta.get_fields()
    changed = False
    previous_values = []
    for field in fields:
        new_value = getattr(IrapToolDataImport, field.name)
        old_value = getattr(IrapToolData, field.name)
        if old_value != new_value:
            changed = True
            setattr(new, field.name, new_value)
        previous_values.append(
            {
                "key": field.name,
                "previous_value": old_value,
            }
        )
        return changed, previous_values


def process_import():
    """To be called after the irap data has been imported successfully from DW"""
    IrapToolData.objects.update(
        imported = False
    )

    imported_iraps = IrapToolDataImport.objects.all()
    for imported_irap in imported_iraps:
        irap, created = IrapToolData.objects.get_or_create(
            product_irap_reference_number=imported_irap.product_irap_reference_number
        )
        irap.imported = True

        if created:
            # Easy case, a new record found
            irap.product_name = imported_irap.product_name
            irap.functionality = imported_irap.functionality
            irap.AfterImportStatus = IrapToolData.AfterImportStatus.NEW
        else:
            changed, changes = diff_irap_data(imported_irap, irap)
            match irap.AfterImportStatus:
                case IrapToolData.AfterImportStatus.REVIEWED:
                    if changed:
                        irap.AfterImportStatus = IrapToolData.AfterImportStatus.CHANGED
                        irap.previous_fields = changes

                case IrapToolData.AfterImportStatus.DELETED:
                    # This record was deleted at last import,
                    # but the deletion was not reviewed
                    irap.AfterImportStatus = IrapToolData.AfterImportStatus.UNDELETED
                    irap.previous_fields = changes

        irap.save()
        # Mark the deleted records: they exist in the irap table
        # but don't exist in the imported data
        deleted_iraps = IrapToolData.objects.filter(imported=True)
        for deleted_irap in deleted_iraps:
            if Tool.objects.filter(irap_tool=deleted_irap.pk):
                # If this deleted record was used in the tool page,
                # mark it as deleted and let the tool administrator
                # handle the page.
                IrapToolData.objects.filter(imported=True).update(
                    AfterImportStatus = IrapToolData.AfterImportStatus.DELETED,
                    imported = True
                )
                deleted_irap.save()
            else:
                # If the deleted record was not used in the tool page,
                # delete it. None will miss it!
                deleted_irap.delete()


def complete_irap_review(irap):
    # This will be used after the tool administrator has checked
    # the irap record.
    # If the record was not available in the last import,
    # it gets deleted
    # Otherwise it is marked as 'REVIEWED'
    if irap.AfterImportStatus == IrapToolData.AfterImportStatus.DELETED:
        irap.delete()
    else:
        irap.AfterImportStatus = IrapToolData.AfterImportStatus.REVIEWED
        irap.previous_fields = None
        irap.savesave()
