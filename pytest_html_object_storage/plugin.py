import os

from _pytest.config import Config
from _pytest.config.argparsing import Parser

from pytest_html_object_storage.minio import HTMLMinio
from pytest_html_object_storage.obs import HTMLObs
from pytest_html_object_storage.swift import HTMLSwift


def pytest_addoption(parser: Parser):
    parser.addoption(
        "--store-minio",
        action="store_true",
        help="send HTML report via MinIO",
    )
    parser.addoption(
        "--store-swift",
        action="store_true",
        help="send HTML report via Swift",
    )
    parser.addoption(
        "--store-obs",
        action="store_true",
        help="send HTML report via OBS",
    )


def pytest_configure(config: Config):
    if config.getoption("--store-minio") and not hasattr(config, "workerinput"):
        if (
            not os.environ.get("OBJECT_STORAGE_ENDPOINT")
            or not os.environ.get("OBJECT_STORAGE_BUCKET")
            or not os.environ.get("OBJECT_STORAGE_USERNAME")
            or not os.environ.get("OBJECT_STORAGE_PASSWORD")
        ):
            raise Exception(
                "You must set the environment variables for html_minio plugin"
            )
        config._html_minio = HTMLMinio(config)
        config.pluginmanager.register(config._html_minio)

    if config.getoption("--store-swift") and not hasattr(config, "workerinput"):
        if (
            not os.environ.get("OBJECT_STORAGE_ENDPOINT")
            or not os.environ.get("OBJECT_STORAGE_BUCKET")
            or not os.environ.get("OBJECT_STORAGE_USERNAME")
            or not os.environ.get("OBJECT_STORAGE_PASSWORD")
            or not os.environ.get("OBJECT_STORAGE_TENANT_ID")
            or not os.environ.get("OBJECT_STORAGE_TENANT_NAME")
            or not os.environ.get("OBJECT_STORAGE_REGION_NAME")
        ):
            raise Exception(
                "You must set the environment variables for html_swift plugin"
            )
        config._html_swift = HTMLSwift(config)
        config.pluginmanager.register(config._html_swift)

    if config.getoption("--store-obs") and not hasattr(config, "workerinput"):
        if (
            not os.environ.get("OBJECT_STORAGE_ENDPOINT")
            or not os.environ.get("OBJECT_STORAGE_BUCKET")
            or not os.environ.get("OBJECT_STORAGE_USERNAME")
            or not os.environ.get("OBJECT_STORAGE_PASSWORD")
            or not os.environ.get("OBJECT_STORAGE_REGION_NAME")
        ):
            raise Exception(
                "You must set the environment variables for html_obs plugin"
            )
        config._html_obs = HTMLObs(config)
        config.pluginmanager.register(config._html_obs)


def pytest_unconfigure(config: Config):
    html_minio = getattr(config, "_html_minio", None)
    if html_minio:
        del config._html_minio
        config.pluginmanager.unregister(html_minio)

    html_swift = getattr(config, "_html_swift", None)
    if html_swift:
        del config._html_swift
        config.pluginmanager.unregister(html_swift)

    html_obs = getattr(config, "_html_obs", None)
    if html_obs:
        del config._html_obs
        config.pluginmanager.unregister(html_obs)
