from unittest.mock import patch

from mint.cli import main, render_help


def test_render_help_lists_all_commands():
    h = render_help()
    assert "add" in h
    assert "clean" in h
    assert "help" in h
    assert "Usage:" in h
    assert "Commands:" in h


def test_cli_no_args_prints_banner_and_help(capsys):
    rc = main([])
    out = capsys.readouterr().out
    assert "mint" in out.lower()
    assert "add" in out
    assert "clean" in out
    assert "Usage:" in out
    assert rc != 0


def test_cli_help_command_returns_zero(capsys):
    rc = main(["help"])
    out = capsys.readouterr().out
    assert "Usage:" in out
    assert rc == 0


def test_cli_add_dispatches():
    with patch("mint.cli.run_add") as r:
        r.return_value.imported = 1
        r.return_value.skipped = 0
        r.return_value.failed = 0
        r.return_value.failed_titles = []
        rc = main(["add", "https://youtube.com/watch?v=abc123"])
    assert rc == 0
    r.assert_called_once()


def test_cli_clean_dispatches():
    with patch("mint.cli.run_clean") as r:
        r.return_value.applied = 0
        r.return_value.aborted = False
        rc = main(["clean"])
    assert rc == 0
    r.assert_called_once()


def test_cli_dup_dispatches():
    with patch("mint.cli.run_dup") as r:
        r.return_value.groups = 0
        r.return_value.extra_files = 0
        rc = main(["dup"])
    assert rc == 0
    r.assert_called_once()


def test_cli_update_dispatches():
    with patch("mint.cli.run_update") as r:
        r.return_value.method = "pipx"
        r.return_value.returncode = 0
        rc = main(["update"])
    assert rc == 0
    r.assert_called_once()
