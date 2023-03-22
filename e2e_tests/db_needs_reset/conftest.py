import pytest
from ..db_utils import recreate_db
from ..utils import populate_db


@pytest.fixture(scope="function", autouse=True)
def recreate_db_from_test_template(django_db_blocker):
    recreate_db()
    populate_db(django_db_blocker)
