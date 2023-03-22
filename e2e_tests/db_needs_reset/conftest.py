import pytest
from ..db_utils import recreate_db


@pytest.fixture(scope="function", autouse=True)
def recreate_db_from_test_template():
    recreate_db()
