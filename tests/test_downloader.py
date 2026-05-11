from unittest.mock import patch

from mint.downloader import download_url


def test_download_url_runs_spotdl_in_output_dir(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "Track A.mp3").write_bytes(b"x")
    (staging / "Track B.mp3").write_bytes(b"y")

    with patch("mint.downloader.subprocess.run") as run:
        run.return_value.returncode = 0
        paths = download_url("https://open.spotify.com/album/abc", staging)

    args = run.call_args[0][0]
    assert args[0] == "spotdl"
    assert "https://open.spotify.com/album/abc" in args
    assert sorted(p.name for p in paths) == ["Track A.mp3", "Track B.mp3"]


def test_download_url_returns_empty_when_no_files_downloaded(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    with patch("mint.downloader.subprocess.run") as run:
        run.return_value.returncode = 0
        paths = download_url("https://open.spotify.com/album/abc", staging)
    assert paths == []
