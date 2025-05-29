import json

from django.conf import settings

from data_flow_s3_import.ingest import DataFlowS3IngestToModel
from data_flow_s3_import.types import PrimaryKey
from peoplefinder.models import DBTSector, UKOfficeLocation


class DBTSectorsS3Ingest(DataFlowS3IngestToModel):
    export_bucket: str = settings.DATA_FLOW_UPLOADS_BUCKET
    export_path: str = settings.DATA_FLOW_UPLOADS_BUCKET_PATH
    export_directory: str = settings.DATA_FLOW_DBT_SECTORS_DIRECTORY
    model = DBTSector
    identifier_field_name = "sector_id"
    identifier_field_object_mapping = "field_01"
    mapping = {
        "sector_id": "field_01",
        "full_sector_name": "full_sector_name",
        "sector_cluster_name_april_2023_onwards": "sector_cluster__april_2023",
        "sector_cluster_name_before_april_2023": "field_03",
        "sector_name": "field_04",
        "sub_sector_name": "field_05",
        "sub_sub_sector_name": "field_02",
        "start_date": "field_06",
        "end_date": "field_07",
    }

    def process_row(self, line: str) -> PrimaryKey:
        """
        Takes a row of the file, retrieves a dict of the instance it refers to and hands that off for processing
        """
        obj: dict = json.loads(s=line)  # DBTSector does not wrap content in 'object'
        return self._process_object_workflow(obj=obj)


class UkOfficeLocationsS3Ingest(DataFlowS3IngestToModel):
    export_bucket: str = settings.DATA_FLOW_UPLOADS_BUCKET
    export_path: str = settings.DATA_FLOW_UPLOADS_BUCKET_PATH
    export_directory: str = settings.DATA_FLOW_UK_OFFICE_LOCATIONS_DIRECTORY
    model = UKOfficeLocation
    identifier_field_name = "code"
    identifier_field_object_mapping = "location_code"
    mapping = {
        "code": "location_code",
        "name": "location_name",
        "city": "city",
        "organisation": "organisation",
        "building_name": "building_name",
    }

    def process_row(self, line: str) -> PrimaryKey:
        """
        Takes a row of the file, retrieves a dict of the instance it refers to and hands that off for processing
        """
        obj: dict = json.loads(
            s=line
        )  # UkOfficeLocation does not wrap content in 'object'
        return self._process_object_workflow(obj=obj)
