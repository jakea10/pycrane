import pytest
import json
import os
import tempfile

from pycrane import ContainerImage, get_config


def test_get_config():
    sample_image_data = [
        {
            "name": "my-image",
            "tag": "latest",
            "source_repo": "registry.source.com/my-image",
            "target_repo": "registry.target.com/my-image"
        },
        {
            "name": "another-image",
            "tag": "1.2.3",
            "source_repo": "registry.source.com/another-image",
            "target_repo": "registry.target.com/another-image"
        }
    ]
    expected_config = {
        'SOURCE_REGISTRY_URL': 'registry.source.com',
        'SOURCE_REGISTRY_USER': 'sourceUser',
        'SOURCE_REGISTRY_KEY': 'sourceKey',
        'TARGET_REGISTRY_URL': 'registry.target.com',
        'TARGET_REGISTRY_USER': 'targetUser',
        'TARGET_REGISTRY_KEY': 'targetKey',
        'IMAGES': [
            ContainerImage.from_dict(sample_image_data[0]),
            ContainerImage.from_dict(sample_image_data[1])
        ]
    }

    os.environ["SOURCE_REGISTRY_URL"] = "registry.source.com"
    os.environ["SOURCE_REGISTRY_USER"] = "sourceUser"
    os.environ["SOURCE_REGISTRY_KEY"] = "sourceKey"

    os.environ["TARGET_REGISTRY_URL"] = "registry.target.com"
    os.environ["TARGET_REGISTRY_USER"] = "targetUser"
    os.environ["TARGET_REGISTRY_KEY"] = "targetKey"

    with tempfile.NamedTemporaryFile(delete_on_close=False, mode='w+') as f:
        json.dump(sample_image_data, f)
        f.flush()
        config = get_config(f.name)

    assert config == expected_config