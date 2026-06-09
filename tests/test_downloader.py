from unittest.mock import patch

from mint.downloader import DownloadedTrack, _clean_uploader, download_url


def test_clean_uploader_strips_topic():
    assert _clean_uploader("Marlon Funaki - Topic") == "Marlon Funaki"


def test_clean_uploader_strips_vevo():
    assert _clean_uploader("ColdplayVEVO") == "Coldplay"


def test_clean_uploader_passthrough():
    assert _clean_uploader("Some Channel") == "Some Channel"


def test_download_url_runs_yt_dlp_in_output_dir(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "abc123.mp3").write_bytes(b"x")
    (staging / "def456.mp3").write_bytes(b"y")

    def _fake_run(*a, **k):
        (staging / ".titles.tsv").write_text(
            "abc123\tArtist A - Track A\tA Channel\tNA\tNA\tNA\tNA\tNA\tNA\n"
            "def456\tAlready Home\tMarlon Funaki - Topic\tMarlon Funaki\tAlready Home\tNA\tNA\tNA\tNA\n"
        )
        class _R:
            returncode = 0
        return _R()

    with patch("mint.downloader.subprocess.run", side_effect=_fake_run) as run:
        tracks = download_url("https://youtube.com/watch?v=abc123", staging)

    args = run.call_args[0][0]
    assert args[1] == "-m"
    assert args[2] == "yt_dlp"
    assert "https://youtube.com/watch?v=abc123" in args
    assert "-x" in args
    fmt_idx = args.index("--audio-format")
    assert args[fmt_idx + 1] == "mp3"

    by_name = {t.path.name: t for t in tracks}
    assert by_name["abc123.mp3"].title == "Artist A - Track A"
    assert by_name["abc123.mp3"].uploader == "A Channel"
    assert by_name["abc123.mp3"].artist == ""
    assert by_name["def456.mp3"].title == "Already Home"
    assert by_name["def456.mp3"].uploader == "Marlon Funaki"
    assert by_name["def456.mp3"].artist == "Marlon Funaki"
    assert by_name["def456.mp3"].track == "Already Home"


def test_download_url_captures_playlist_metadata(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "vid1.mp3").write_bytes(b"x")
    (staging / "vid2.mp3").write_bytes(b"y")

    def _fake_run(*a, **k):
        (staging / ".titles.tsv").write_text(
            "vid1\tDrake - Rich Flex\tDrakeVEVO\tDrake\tRich Flex\tHer Loss\t"
            "PL123\tHer Loss\tDrake - Topic\n"
            "vid2\tDrake - Major Distribution\tDrakeVEVO\tDrake\tMajor Distribution\tHer Loss\t"
            "PL123\tHer Loss\tDrake - Topic\n"
        )
        class _R:
            returncode = 0
        return _R()

    with patch("mint.downloader.subprocess.run", side_effect=_fake_run):
        tracks = download_url("https://youtube.com/watch?v=vid1&list=PL123", staging)

    by_name = {t.path.name: t for t in tracks}
    t1 = by_name["vid1.mp3"]
    assert t1.playlist_id == "PL123"
    assert t1.playlist_title == "Her Loss"
    assert t1.playlist_uploader == "Drake"
    assert t1.artist == "Drake"
    assert t1.track == "Rich Flex"


def test_download_url_returns_empty_when_no_files_downloaded(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    with patch("mint.downloader.subprocess.run") as run:
        run.return_value.returncode = 0
        tracks = download_url("https://youtube.com/watch?v=abc", staging)
    assert tracks == []


def test_download_url_falls_back_to_stem_when_titles_missing(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "xyz.mp3").write_bytes(b"x")

    with patch("mint.downloader.subprocess.run") as run:
        run.return_value.returncode = 0
        tracks = download_url("https://youtube.com/watch?v=xyz", staging)

    assert len(tracks) == 1
    assert tracks[0].path == staging / "xyz.mp3"
    assert tracks[0].title == "xyz"
    assert tracks[0].uploader == ""
