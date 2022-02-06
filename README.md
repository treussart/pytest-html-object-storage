# pytest-html-object-storage

Pytest report plugin for send HTML report on object-storage

Allow to send HTML report on object-storage.

## Implementations

* [MinIO](https://min.io/)
* [Swift](https://docs.openstack.org/python-swiftclient/newton/swiftclient.html) (tested with OVH)
* [OBS](https://github.com/huaweicloud/huaweicloud-sdk-python-obs) (tested with Orange Flexible Engine)

## installation

    pip install pytest-html-object-storage

## Configure via env var

### Common

    OBJECT_STORAGE_ENDPOINT="localhost:9000"
    OBJECT_STORAGE_BUCKET="bucket"
    OBJECT_STORAGE_USERNAME="admin"
    OBJECT_STORAGE_PASSWORD="password"
    OBJECT_STORAGE_REGION_NAME=""

### Common Optional

    OBJECT_STORAGE_POLICY="private"
    OBJECT_STORAGE_RETENTION="30" // day unit

### Specific MinIO

#### Optional

    OBJECT_STORAGE_SECURE="false"

### Specific Swift

    OBJECT_STORAGE_TENANT_ID=""
    OBJECT_STORAGE_TENANT_NAME=""

## Add option to send HTML report

### MinIO

    pytest --store-minio

### Swift

    pytest --store-swift

### OBS

    pytest --store-obs


## Dev

### Change version

edit

    pytest_html_object_storage/__init__.py

commit

    git commit -m "v0.1.0"

tag

    git tag v0.1.0

### Build package

    python -m build
    twine upload dist/*
