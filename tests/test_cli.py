from unittest.mock import patch

from mint.cli import main


def test_cli_no_args_prints_banner_and_usage(capsys):
    rc = main([])
    out = capsys.readouterr().out
    assert "mint" in out.lower()
    assert "add" in out
    assert "fix" in out
    assert rc != 0


def test_cli_add_dispatches(capsys):
    with patch("mint.cli.run_add") as r:
        r.return_value.imported = 1
        r.return_value.skipped = 0
        r.return_value.failed = 0
        r.return_value.failed_titles = []
        rc = main(["add", "https://open.spotify.com/track/x"])
    assert rc == 0
    r.assert_called_once()


def test_cli_fix_dispatches():
    with patch("mint.cli.run_fix") as r:
        r.return_value.applied = 0
        r.return_value.aborted = False
        rc = main(["fix"])
    assert rc == 0
    r.assert_called_once()
