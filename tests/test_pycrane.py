# tests/test_pycrane.py

import pytest
import json
from typer.testing import CliRunner
from pathlib import Path
from typing import List
from pycrane import __app_name__, __version__, cli
from pycrane.pycrane import ContainerImage


runner = CliRunner()


def test_version():
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0
    assert f"{__app_name__} v{__version__}\n" in result.stdout
    result = runner.invoke(cli.app, ["-v"])
    assert result.exit_code == 0
    assert f"{__app_name__} v{__version__}\n" in result.stdout


image_data = [
    {
        "name": "my-app/web",
        "tag": "latest",
        "source_repo": "registry.source.com/apps/my-app/web",
        "target_repo": "registry.target.com/my-app/web",
    },
    {
        "name": "another-app/server",
        "tag": "1.2.3",
        "source_repo": "registry.source.com/apps/another-app/server",
        "target_repo": "registry.target.com/another-app/server",
    },
    {
        "name": "nginx",
        "tag": "latest",
        "source_repo": "registry.source.com/nginx",
        "target_repo": "registry.target.com/nginx",
    },
]


@pytest.fixture
def mock_image_file(tmp_path: Path):
    image_file = tmp_path / "images.json"
    with image_file.open("w") as f:
        json.dump(image_data, f)
    return image_file


def test_parse_images(mock_image_file):
    images: List[ContainerImage] = cli._parse_images(mock_image_file)
    assert len(images) == 3
    for image in images:
        assert type(image) is ContainerImage
