from tools.models import IrapToolData, IrapToolDataImport, Tool


def update_irap_data(old: IrapToolData, new: IrapToolDataImport) -> tuple[bool, {}, {}]:
    # Copies all the existing values to the previous values dictionary,
    # so they can be displayed to the tool admin when the changes
    # are reviewed
    # The format may not be the best, but it can be reviewed when
    # it  has to be displayed

    new_fields = new._meta.get_fields()
    changed = False
    previous_values = {}
    for field in new_fields:
        new_value = getattr(new, field.name)
        old_value = getattr(old, field.name)
        if old_value != new_value:
            changed = True
            setattr(old, field.name, new_value)
        previous_values[field.name] = old_value

    return changed, previous_values


def are_field_identical(import_obj: IrapToolDataImport, old_values: dict) -> bool:
    for key in old_values.keys():
        if getattr(import_obj, key) != old_values[key]:
            return False
    return True


def process_import():
    """To be called after the irap data has been imported
    successfully from Data Workspace.
    There is no validation on the new records, as any validation will
    happen when the data is imported from DW
    """
    IrapToolData.objects.update(imported=False)

    imported_iraps = IrapToolDataImport.objects.all()
    for imported_irap in imported_iraps:
        irap, created = IrapToolData.objects.get_or_create(
            product_irap_reference_number=imported_irap.product_irap_reference_number
        )

        if created:
            # Easy case, a new record found
            irap.product_name = imported_irap.product_name
            irap.functionality = imported_irap.functionality
            irap.after_import_status = IrapToolData.AfterImportStatus.NEW
        else:
            changed, changes = update_irap_data(irap, imported_irap)
            match irap.after_import_status:
                case IrapToolData.AfterImportStatus.REVIEWED:
                    if changed:
                        irap.after_import_status = (
                            IrapToolData.AfterImportStatus.CHANGED
                        )
                        irap.previous_fields = changes

                case IrapToolData.AfterImportStatus.DELETED:
                    # This record was deleted at last import,
                    # but the deletion was not reviewed
                    irap.after_import_status = IrapToolData.AfterImportStatus.UNDELETED
                    irap.previous_fields = changes

                case IrapToolData.AfterImportStatus.CHANGED:
                    # This record was changed at last import,
                    # but the changes were not reviewed
                    # check that the record has not been restored to what it was
                    # if so, mark it as unchanged
                    older_values = irap.previous_fields
                    if are_field_identical(imported_irap, older_values):
                        irap.after_import_status = (
                            IrapToolData.AfterImportStatus.REVIEWED
                        )
                        irap.previous_fields = None
        irap.imported = True
        irap.save()

    # Mark the deleted records: they exist in the irap table
    # but don't exist in the imported data
    deleted_iraps = IrapToolData.objects.filter(imported=False)
    for deleted_irap in deleted_iraps:
        if Tool.objects.filter(irap_tool=deleted_irap.pk):
            # If this deleted record was used in the tool page,
            # mark it as deleted and let the tool administrator
            # handle the page.
            # deleted_irap.update(
            #     after_import_status=IrapToolData.AfterImportStatus.DELETED,
            #     imported=True,
            # )
            deleted_irap.after_import_status = IrapToolData.AfterImportStatus.DELETED
            deleted_irap.imported = True
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
    if irap.after_import_status == IrapToolData.AfterImportStatus.DELETED:
        irap.delete()
    else:
        irap.after_import_status = IrapToolData.AfterImportStatus.REVIEWED
        irap.previous_fields = None
        irap.savesave()
