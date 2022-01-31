import os

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def set_env():
    os.environ["OBJECT_STORAGE_ENDPOINT"] = "enm1n5rid50yi.x.pipedream.net"
    os.environ["OBJECT_STORAGE_BUCKET"] = "test"
    os.environ["OBJECT_STORAGE_USERNAME"] = "admin"
    os.environ["OBJECT_STORAGE_PASSWORD"] = "password"
    yield
    del os.environ["OBJECT_STORAGE_ENDPOINT"]
    del os.environ["OBJECT_STORAGE_BUCKET"]
    del os.environ["OBJECT_STORAGE_USERNAME"]
    del os.environ["OBJECT_STORAGE_PASSWORD"]
