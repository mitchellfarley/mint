from pathlib import Path
from unittest.mock import patch

from mint.commands.add import run_add
from mint.downloader import DownloadedTrack
from mint.models import MBRelease, MBTrack


def _fake_release():
    return MBRelease(
        release_id="rid-1",
        artist_credit_phrase="Gorillaz",
        title="Demon Days",
        year="2005",
        tracks={
            (1, 6): MBTrack(disc=1, position=6, title="Feel Good Inc.",
                            total_tracks=15, total_discs=1),
        },
        candidate_release_ids=["rid-1"],
    )


def _dl(path, title="", uploader="", artist="", track="",
        playlist_id="", playlist_title="", playlist_uploader=""):
    return DownloadedTrack(
        path=path, title=title, uploader=uploader,
        artist=artist, track=track,
        playlist_id=playlist_id,
        playlist_title=playlist_title,
        playlist_uploader=playlist_uploader,
    )


def test_run_add_pipeline_imports_new_track(tmp_path, make_mp3):
    library_root = tmp_path / "Library"
    library_root.mkdir()
    staging = tmp_path / "staging"
    staging.mkdir()
    staged = make_mp3(name=str(staging / "abc123.mp3"))

    with patch("mint.commands.add.download_url") as dl, \
         patch("mint.commands.add.MBClient") as mbc, \
         patch("mint.commands.add.import_file") as imp:
        dl.return_value = [_dl(staged, title="Gorillaz - Feel Good Inc. (Official Video)")]
        mbc.return_value.lookup_recording.return_value = (_fake_release(), 1, 6)
        mbc.return_value.fetch_cover.return_value = b"\xff\xd8jpeg" + b"\x00" * 100
        imp.return_value = 0
        summary = run_add(
            youtube_url="https://youtube.com/watch?v=abc123",
            library_root=library_root,
            staging_dir=staging,
            cache_db=tmp_path / "mb.db",
            user_agent=("mint", "test", "x@y.z"),
        )

    final = library_root / "Gorillaz" / "Demon Days" / "06 Feel Good Inc..mp3"
    assert final.exists()
    assert summary.imported == 1
    assert summary.failed == 0
    imp.assert_called_once()


def test_run_add_skips_existing_duplicates(tmp_path, make_mp3):
    library_root = tmp_path / "Library"
    (library_root / "Gorillaz" / "Demon Days").mkdir(parents=True)
    make_mp3(name=str(library_root / "Gorillaz" / "Demon Days" / "06 Feel Good Inc..mp3"),
             tit2="Feel Good Inc.", tpe1="Gorillaz", tpe2="Gorillaz",
             talb="Demon Days")

    staging = tmp_path / "staging"
    staging.mkdir()
    staged = make_mp3(name=str(staging / "abc123.mp3"))

    with patch("mint.commands.add.download_url") as dl, \
         patch("mint.commands.add.MBClient"), \
         patch("mint.commands.add.import_file"):
        dl.return_value = [_dl(staged, title="Gorillaz - Feel Good Inc.")]
        summary = run_add(
            youtube_url="https://youtube.com/watch?v=abc123",
            library_root=library_root,
            staging_dir=staging,
            cache_db=tmp_path / "mb.db",
            user_agent=("mint", "test", "x@y.z"),
        )

    assert summary.imported == 0
    assert summary.skipped == 1
    assert not staged.exists()


def test_run_add_reports_unparseable_title(tmp_path, make_mp3):
    library_root = tmp_path / "Library"
    library_root.mkdir()
    staging = tmp_path / "staging"
    staging.mkdir()
    staged = make_mp3(name=str(staging / "xyz.mp3"))

    with patch("mint.commands.add.download_url") as dl, \
         patch("mint.commands.add.MBClient"), \
         patch("mint.commands.add.import_file"):
        dl.return_value = [_dl(staged, title="RANDOM_TITLE_WITH_NO_SEPARATOR")]
        summary = run_add(
            youtube_url="https://youtube.com/watch?v=xyz",
            library_root=library_root,
            staging_dir=staging,
            cache_db=tmp_path / "mb.db",
            user_agent=("mint", "test", "x@y.z"),
        )

    assert summary.imported == 0
    assert summary.failed == 1
    assert "RANDOM_TITLE_WITH_NO_SEPARATOR" in summary.failed_titles[0]


def test_run_add_uses_ytmusic_artist_and_track_fields(tmp_path, make_mp3):
    library_root = tmp_path / "Library"
    library_root.mkdir()
    staging = tmp_path / "staging"
    staging.mkdir()
    staged = make_mp3(name=str(staging / "abc.mp3"))

    with patch("mint.commands.add.download_url") as dl, \
         patch("mint.commands.add.MBClient") as mbc, \
         patch("mint.commands.add.import_file"):
        dl.return_value = [_dl(staged, title="Feel Good Inc.",
                               uploader="Gorillaz - Topic",
                               artist="Gorillaz", track="Feel Good Inc.")]
        mbc.return_value.lookup_recording.return_value = (_fake_release(), 1, 6)
        mbc.return_value.fetch_cover.return_value = None
        summary = run_add(
            youtube_url="https://youtube.com/watch?v=abc",
            library_root=library_root,
            staging_dir=staging,
            cache_db=tmp_path / "mb.db",
            user_agent=("mint", "test", "x@y.z"),
        )

    assert summary.imported == 1
    args, _ = mbc.return_value.lookup_recording.call_args
    assert args == ("Gorillaz", "Feel Good Inc.")


def _fake_release_alt(rid="rid-2", title="Compilation"):
    return MBRelease(
        release_id=rid,
        artist_credit_phrase="Various Artists",
        title=title,
        year="2022",
        tracks={
            (1, 1): MBTrack(disc=1, position=1, title="Feel Good Inc.",
                            total_tracks=20, total_discs=1),
        },
        candidate_release_ids=[rid],
    )


def test_run_add_prompter_picks_second_candidate(tmp_path, make_mp3):
    library_root = tmp_path / "Library"
    library_root.mkdir()
    staging = tmp_path / "staging"
    staging.mkdir()
    staged = make_mp3(name=str(staging / "abc123.mp3"))

    chosen_release = _fake_release_alt(rid="rid-2", title="Compilation")
    fake_candidates = [
        {"recording_id": "r1", "release_id": "rid-1", "artist": "Gorillaz",
         "title": "Demon Days", "year": "2005", "type": "Album", "country": "US",
         "quality": 0},
        {"recording_id": "r2", "release_id": "rid-2", "artist": "Various Artists",
         "title": "Compilation", "year": "2022", "type": "Album", "country": "GB",
         "quality": 0},
        {"recording_id": "r3", "release_id": "rid-3", "artist": "Gorillaz",
         "title": "Demon Days (Deluxe)", "year": "2006", "type": "Album",
         "country": "US", "quality": 0},
    ]

    def fake_lookup(artist, title, prompter=None):
        assert prompter is not None
        idx = prompter(fake_candidates)
        assert idx == 1
        return chosen_release, 1, 1

    prompter_calls: list[list[dict]] = []

    def test_prompter(candidates):
        prompter_calls.append(candidates)
        return 1

    with patch("mint.commands.add.download_url") as dl, \
         patch("mint.commands.add.MBClient") as mbc, \
         patch("mint.commands.add.import_file") as imp:
        dl.return_value = [_dl(staged, title="Gorillaz - Feel Good Inc.")]
        mbc.return_value.lookup_recording.side_effect = fake_lookup
        mbc.return_value.fetch_cover.return_value = None
        imp.return_value = 0
        summary = run_add(
            youtube_url="https://youtube.com/watch?v=abc123",
            library_root=library_root,
            staging_dir=staging,
            cache_db=tmp_path / "mb.db",
            user_agent=("mint", "test", "x@y.z"),
            prompter=test_prompter,
        )

    assert summary.imported == 1
    assert len(prompter_calls) == 1
    assert prompter_calls[0][1]["release_id"] == "rid-2"
    final = library_root / "Various Artists" / "Compilation" / "01 Feel Good Inc..mp3"
    assert final.exists()


def test_run_add_falls_back_to_uploader_when_title_unparseable(tmp_path, make_mp3):
    library_root = tmp_path / "Library"
    library_root.mkdir()
    staging = tmp_path / "staging"
    staging.mkdir()
    staged = make_mp3(name=str(staging / "abc.mp3"))

    with patch("mint.commands.add.download_url") as dl, \
         patch("mint.commands.add.MBClient") as mbc, \
         patch("mint.commands.add.import_file"):
        dl.return_value = [_dl(staged, title="Already Home",
                               uploader="Marlon Funaki")]
        mbc.return_value.lookup_recording.return_value = (_fake_release(), 1, 6)
        mbc.return_value.fetch_cover.return_value = None
        run_add(
            youtube_url="https://youtube.com/watch?v=abc",
            library_root=library_root,
            staging_dir=staging,
            cache_db=tmp_path / "mb.db",
            user_agent=("mint", "test", "x@y.z"),
        )

    args, _ = mbc.return_value.lookup_recording.call_args
    assert args == ("Marlon Funaki", "Already Home")
