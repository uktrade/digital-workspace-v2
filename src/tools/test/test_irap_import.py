from django.test import TestCase


from tools.models import IrapToolDataImport, IrapToolData
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
        self.assertEqual(
        IrapToolDataImport.objects.all().count(),
            RECORD_CREATED
        )
        self.assertEqual(
        IrapToolData.objects.all().count(),
            0
        )
        process_import()
        self.assertEqual(
        IrapToolDataImport.objects.all().count(),
            RECORD_CREATED
        )
        records_in_irap_table = IrapToolData.objects.all().count()
        self.assertEqual(
            records_in_irap_table,
            RECORD_CREATED,
        )
        self.assertEqual(
            IrapToolData.objects.filter(after_import_status=IrapToolData.AfterImportStatus.NEW).count(),
            RECORD_CREATED,
        )

    def test_update(self):
        self.populate_table(IrapToolDataImport)
        self.populate_table(IrapToolData)
        IrapToolData.objects.update(after_import_status=IrapToolData.AfterImportStatus.REVIEWED)
        old_product_name = "New name"
        # Change a record in one table, to see if the changes get picked
        update_record = IrapToolData.objects.get(product_irap_reference_number=FIRST_REFERENCE)
        update_record.product_name = old_product_name
        update_record.save()
        process_import()
        # There should be one record  flagged changed
        self.assertEqual(
            IrapToolData.objects.filter(after_import_status=IrapToolData.AfterImportStatus.CHANGED).count(),
            1,
        )
        self.assertEqual(
            IrapToolData.objects.filter(after_import_status=IrapToolData.AfterImportStatus.REVIEWED).count(),
            RECORD_CREATED - 1,
        )

        changed_obj = IrapToolData.objects.get(after_import_status=IrapToolData.AfterImportStatus.CHANGED)
        self.assertEqual(
            changed_obj.product_irap_reference_number,
            FIRST_REFERENCE
        )
        self.assertNotEqual(
            changed_obj.product_name,
            old_product_name
        )

    def test_delete(self):
        self.populate_table(IrapToolDataImport, RECORD_CREATED-1)
        self.populate_table(IrapToolData)
        IrapToolData.objects.update(
            after_import_status=IrapToolData.AfterImportStatus.REVIEWED)

        self.assertEqual(
            IrapToolData.objects.all().count(),
            RECORD_CREATED,
        )

        process_import()

        # There should be one record marked 'DELETED'
        self.assertEqual(
            IrapToolData.objects.all().count(),
            RECORD_CREATED-1,
        )


