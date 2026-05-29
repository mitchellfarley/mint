from unittest.mock import patch

from mint.commands.shell_init import (
    MARKER_BEGIN,
    _detect_rc,
    run_shell_init,
)


def test_detect_rc_zsh(monkeypatch, tmp_path):
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setattr("mint.commands.shell_init.Path.home", lambda: tmp_path)
    rc, snippet = _detect_rc()
    assert rc == tmp_path / ".zshrc"
    assert "noglob command mint" in snippet


def test_detect_rc_bash(monkeypatch, tmp_path):
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.setattr("mint.commands.shell_init.Path.home", lambda: tmp_path)
    rc, _ = _detect_rc()
    assert rc == tmp_path / ".bashrc"


def test_run_shell_init_prints_without_install(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setattr("mint.commands.shell_init.Path.home", lambda: tmp_path)
    result = run_shell_init(install=False)
    out = capsys.readouterr().out
    assert "noglob command mint" in out
    assert result.installed is False
    assert not (tmp_path / ".zshrc").exists()


def test_run_shell_init_installs_when_missing(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setattr("mint.commands.shell_init.Path.home", lambda: tmp_path)
    (tmp_path / ".zshrc").write_text("export FOO=bar\n")
    result = run_shell_init(install=True)
    content = (tmp_path / ".zshrc").read_text()
    assert "export FOO=bar" in content
    assert MARKER_BEGIN in content
    assert "noglob command mint" in content
    assert result.installed is True


def test_run_shell_init_is_idempotent(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setattr("mint.commands.shell_init.Path.home", lambda: tmp_path)
    run_shell_init(install=True)
    capsys.readouterr()
    result = run_shell_init(install=True)
    out = capsys.readouterr().out
    content = (tmp_path / ".zshrc").read_text()
    assert content.count(MARKER_BEGIN) == 1
    assert result.installed is False
    assert result.already_present is True
    assert "Already installed" in out


def test_run_shell_init_creates_rc_if_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setattr("mint.commands.shell_init.Path.home", lambda: tmp_path)
    rc = tmp_path / ".zshrc"
    assert not rc.exists()
    result = run_shell_init(install=True)
    assert rc.exists()
    assert MARKER_BEGIN in rc.read_text()
    assert result.installed is True
