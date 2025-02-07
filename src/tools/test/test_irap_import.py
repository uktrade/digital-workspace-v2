from django.test import TestCase


from tools.models import IrapToolDataImport, IrapToolData, Tool
from tools.import_irap_tool import process_import

RECORD_CREATED = 6
FIRST_REFERENCE = 200


class ImportIrapTestCase(TestCase):
    def populate_table(self, model, record_to_create=RECORD_CREATED):
        for i in range(0, record_to_create):
            model.objects.create(
                product_irap_reference_number=FIRST_REFERENCE + i,
                product_name=f"Product name {i}",
                functionality=f"Functionality {i}",
            )

    def test_new(self):
        self.populate_table(IrapToolDataImport)
        self.assertEqual(IrapToolDataImport.objects.all().count(), RECORD_CREATED)
        self.assertEqual(IrapToolData.objects.all().count(), 0)
        process_import()
        self.assertEqual(IrapToolDataImport.objects.all().count(), RECORD_CREATED)
        records_in_irap_table = IrapToolData.objects.all().count()
        self.assertEqual(
            records_in_irap_table,
            RECORD_CREATED,
        )
        self.assertEqual(
            IrapToolData.objects.filter(
                after_import_status=IrapToolData.AfterImportStatus.NEW
            ).count(),
            RECORD_CREATED,
        )

    def test_update(self):
        self.populate_table(IrapToolDataImport)
        self.populate_table(IrapToolData)
        IrapToolData.objects.update(
            after_import_status=IrapToolData.AfterImportStatus.REVIEWED
        )
        old_product_name = "New name"
        # Change a record in one table, to see if the changes get picked
        update_record = IrapToolData.objects.get(
            product_irap_reference_number=FIRST_REFERENCE
        )
        update_record.product_name = old_product_name
        update_record.save()
        process_import()
        # There should be one record  flagged changed
        self.assertEqual(
            IrapToolData.objects.filter(
                after_import_status=IrapToolData.AfterImportStatus.CHANGED
            ).count(),
            1,
        )
        self.assertEqual(
            IrapToolData.objects.filter(
                after_import_status=IrapToolData.AfterImportStatus.REVIEWED
            ).count(),
            RECORD_CREATED - 1,
        )

        changed_obj = IrapToolData.objects.get(
            after_import_status=IrapToolData.AfterImportStatus.CHANGED
        )
        self.assertEqual(changed_obj.product_irap_reference_number, FIRST_REFERENCE)
        self.assertNotEqual(changed_obj.product_name, old_product_name)

    def test_delete(self):
        self.populate_table(IrapToolDataImport, RECORD_CREATED - 1)
        self.populate_table(IrapToolData)
        IrapToolData.objects.update(
            after_import_status=IrapToolData.AfterImportStatus.REVIEWED
        )

        self.assertEqual(
            IrapToolData.objects.all().count(),
            RECORD_CREATED,
        )
        process_import()

        # There should be one less record
        self.assertEqual(
            IrapToolData.objects.all().count(),
            RECORD_CREATED - 1,
        )

    def test_soft_delete(self):
        self.populate_table(IrapToolDataImport)
        self.populate_table(IrapToolData)
        IrapToolData.objects.update(
            after_import_status=IrapToolData.AfterImportStatus.REVIEWED
        )
        # Remove one record from the import table
        product_irap_reference_number_to_be_deleted = FIRST_REFERENCE
        IrapToolDataImport.objects.get(
            product_irap_reference_number=product_irap_reference_number_to_be_deleted
        ).delete()
        self.assertEqual(
            IrapToolDataImport.objects.all().count(),
            RECORD_CREATED - 1,
        )
        # Create a pge referencing the tool to be deleted
        obj_to_be_deleted = IrapToolData.objects.get(
            product_irap_reference_number=product_irap_reference_number_to_be_deleted
        )
        Tool.objects.create(
            irap_tool=obj_to_be_deleted,
            depth=1,
            title="Title",
            path="Path",
        )

        self.assertEqual(
            IrapToolData.objects.all().count(),
            RECORD_CREATED,
        )
        process_import()

        # No record has been deleted
        self.assertEqual(
            IrapToolData.objects.all().count(),
            RECORD_CREATED,
        )
        #         But there is a record marked deleted
        self.assertEqual(
            IrapToolData.objects.filter(
                after_import_status=IrapToolData.AfterImportStatus.DELETED
            ).count(),
            1,
        )

    def test_undelete(self):
        self.populate_table(IrapToolDataImport)
        self.populate_table(IrapToolData)
        IrapToolData.objects.update(
            after_import_status=IrapToolData.AfterImportStatus.REVIEWED
        )
        IrapToolData.objects.filter(
            product_irap_reference_number=FIRST_REFERENCE
        ).update(after_import_status=IrapToolData.AfterImportStatus.DELETED)

        process_import()

        # No record has been deleted
        self.assertEqual(
            IrapToolData.objects.all().count(),
            RECORD_CREATED,
        )
        undeleted_objs = IrapToolData.objects.filter(
            after_import_status=IrapToolData.AfterImportStatus.UNDELETED
        )
        #         But there is a record marked undeleted
        self.assertEqual(
            undeleted_objs.count(),
            1,
        )

        self.assertEqual(
            undeleted_objs.first().product_irap_reference_number,
            FIRST_REFERENCE,
        )

    def test_record_reset(self):
        # Only create one record in both tables
        IrapToolDataImport.objects.create(
            product_irap_reference_number=FIRST_REFERENCE,
            product_name="Product name changes",
            functionality="Functionality",
        )
        IrapToolData.objects.create(
            product_irap_reference_number=FIRST_REFERENCE,
            product_name="Product name original",
            functionality="Functionality",
            after_import_status=IrapToolData.AfterImportStatus.REVIEWED,
        )
        process_import()
        irap_tool_data = IrapToolData.objects.get(
            product_irap_reference_number=FIRST_REFERENCE
        )

        self.assertEqual(
            irap_tool_data.after_import_status, IrapToolData.AfterImportStatus.CHANGED
        )
        self.assertEqual(irap_tool_data.product_name, "Product name changes")
        self.assertNotEqual(irap_tool_data.previous_fields, None)
        IrapToolDataImport.objects.filter(
            product_irap_reference_number=FIRST_REFERENCE,
        ).update(
            product_name=f"Product name original",
        )

        process_import()
        irap_tool_data = IrapToolData.objects.get(
            product_irap_reference_number=FIRST_REFERENCE
        )

        self.assertEqual(irap_tool_data.product_name, "Product name original")
        # self.assertEqual(
        #     irap_tool_data.previous_fields,
        #     None
        # )

        self.assertEqual(
            irap_tool_data.after_import_status, IrapToolData.AfterImportStatus.REVIEWED
        )
