from unittest.mock import patch

from mint.downloader import download_url


def test_download_url_runs_yt_dlp_in_output_dir(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "abc123.mp3").write_bytes(b"x")
    (staging / "def456.mp3").write_bytes(b"y")
    (staging / ".titles.tsv").write_text("abc123\tArtist A - Track A\ndef456\tArtist B - Track B\n")

    with patch("mint.downloader.subprocess.run") as run:
        run.return_value.returncode = 0
        paths = download_url("https://youtube.com/watch?v=abc123", staging)

    args = run.call_args[0][0]
    assert args[1] == "-m"
    assert args[2] == "yt_dlp"
    assert "https://youtube.com/watch?v=abc123" in args
    assert "-x" in args
    assert "--audio-format" in args
    fmt_idx = args.index("--audio-format")
    assert args[fmt_idx + 1] == "mp3"
    names = sorted((p.name, t) for p, t in paths)
    assert names == [
        ("abc123.mp3", "Artist A - Track A"),
        ("def456.mp3", "Artist B - Track B"),
    ]


def test_download_url_returns_empty_when_no_files_downloaded(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    with patch("mint.downloader.subprocess.run") as run:
        run.return_value.returncode = 0
        paths = download_url("https://youtube.com/watch?v=abc", staging)
    assert paths == []


def test_download_url_falls_back_to_stem_when_titles_missing(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "xyz.mp3").write_bytes(b"x")

    with patch("mint.downloader.subprocess.run") as run:
        run.return_value.returncode = 0
        paths = download_url("https://youtube.com/watch?v=xyz", staging)

    assert paths == [(staging / "xyz.mp3", "xyz")]
