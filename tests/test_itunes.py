from unittest.mock import patch

from mint.itunes import import_file, remove_album


def test_import_file_runs_osascript():
    with patch("mint.itunes.subprocess.run") as run:
        run.return_value.returncode = 0
        import_file("/tmp/song.mp3")
    args = run.call_args[0][0]
    assert args[0] == "osascript"
    assert args[1] == "-e"
    assert "/tmp/song.mp3" in args[2]
    assert "Music" in args[2]


def test_import_file_escapes_double_quotes():
    with patch("mint.itunes.subprocess.run") as run:
        run.return_value.returncode = 0
        import_file('/tmp/She said "hi".mp3')
    args = run.call_args[0][0]
    assert '\\"hi\\"' in args[2]


def test_remove_album_runs_osascript_with_album_name():
    with patch("mint.itunes.subprocess.run") as run:
        run.return_value.returncode = 0
        remove_album("Demon Days")
    args = run.call_args[0][0]
    assert "Demon Days" in args[2]
    assert "delete" in args[2]
