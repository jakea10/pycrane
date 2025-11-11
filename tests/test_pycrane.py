# tests/test_pycrane.py

import pytest
from typer.testing import CliRunner
from pycrane import ___app_name__, __version__, cli


runner = CliRunner()

def test_version():
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0
    assert f"{___app_name__} v{__version__}\n" in result.stdout
    result = runner.invoke(cli.app, ["-v"])
    assert result.exit_code == 0
    assert f"{___app_name__} v{__version__}\n" in result.stdout
