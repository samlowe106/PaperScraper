# conftest.py

import pytest


@pytest.fixture(scope="session")
def vcr_config():
    return {
        "cassette_library_dir": "tests/cassettes",
        "record_mode": "once",
    }
