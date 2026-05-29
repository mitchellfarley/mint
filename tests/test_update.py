import sys
from unittest.mock import patch

from mint.commands.update import _detect_method, run_update


def test_detect_method_returns_pipx_when_in_pipx_path():
    with patch("mint.commands.update.sys") as s, \
         patch("mint.commands.update.shutil") as sh:
        s.executable = "/Users/x/.local/pipx/venvs/mint/bin/python"
        sh.which.return_value = "/usr/local/bin/pipx"
        assert _detect_method() == "pipx"


def test_detect_method_returns_pipx_when_available():
    with patch("mint.commands.update.sys") as s, \
         patch("mint.commands.update.shutil") as sh:
        s.executable = "/usr/local/bin/python3"
        sh.which.return_value = "/usr/local/bin/pipx"
        assert _detect_method() == "pipx"


def test_detect_method_falls_back_to_pip():
    with patch("mint.commands.update.sys") as s, \
         patch("mint.commands.update.shutil") as sh:
        s.executable = "/Users/x/.venv/bin/python"
        sh.which.return_value = None
        assert _detect_method() == "pip"


def test_run_update_calls_pipx_upgrade(capsys):
    with patch("mint.commands.update._detect_method", return_value="pipx"), \
         patch("mint.commands.update.subprocess.run") as run:
        run.return_value.returncode = 0
        result = run_update()
    assert result.method == "pipx"
    assert result.returncode == 0
    cmd = run.call_args[0][0]
    assert cmd == ["pipx", "upgrade", "mint"]


def test_run_update_calls_pip_install_upgrade():
    with patch("mint.commands.update._detect_method", return_value="pip"), \
         patch("mint.commands.update.subprocess.run") as run:
        run.return_value.returncode = 0
        result = run_update()
    assert result.method == "pip"
    cmd = run.call_args[0][0]
    assert cmd[1:] == ["-m", "pip", "install", "--upgrade",
                       "git+https://github.com/mitchellfarley/mint.git"]
