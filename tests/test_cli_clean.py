import io
from pathlib import Path
from unittest.mock import patch

from mint.commands.clean import run_clean
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


def test_run_clean_aborts_when_user_declines(tmp_path, make_mp3, monkeypatch, capsys):
    root = tmp_path / "Library"
    (root / "Gorillaz" / "Demon Days").mkdir(parents=True)
    path = make_mp3(
        name=str(root / "Gorillaz" / "Demon Days" / "06 Feel Good Inc..mp3"),
        tit2="Feel Good Inc.", tpe1="Gorillaz feat. De La Soul",
        tpe2="Gorillaz", talb="Demon Days", tdrc="2005",
        trck="6/15", tpos="", tcon="Alternative Rock",
        apic=b"\xff\xd8jpg" + b"\x00" * 100,
    )
    monkeypatch.setattr("builtins.input", lambda _: "n")

    with patch("mint.commands.clean.MBClient") as mbc:
        mbc.return_value.lookup_release.return_value = _fake_release()
        mbc.return_value.fetch_cover.return_value = None
        result = run_clean(
            library_root=root,
            cache_db=tmp_path / "mb.db",
            user_agent=("mint", "test", "x@y.z"),
        )

    assert result.applied == 0
    out = capsys.readouterr().out
    assert "Apply" in out


def test_run_clean_applies_when_user_approves(tmp_path, make_mp3, monkeypatch):
    root = tmp_path / "Library"
    (root / "Gorillaz" / "Demon Days").mkdir(parents=True)
    path = make_mp3(
        name=str(root / "Gorillaz" / "Demon Days" / "06 Feel Good Inc..mp3"),
        tit2="Feel Good Inc.", tpe1="Gorillaz feat. De La Soul",
        tpe2="Gorillaz", talb="Demon Days", tdrc="2005",
        trck="6/15", tpos="", tcon="Alternative Rock",
        apic=b"\xff\xd8jpg" + b"\x00" * 100,
    )
    monkeypatch.setattr("builtins.input", lambda _: "y")

    with patch("mint.commands.clean.MBClient") as mbc, \
         patch("mint.commands.clean.remove_album") as rm, \
         patch("mint.commands.clean.import_file") as imp:
        mbc.return_value.lookup_release.return_value = _fake_release()
        mbc.return_value.fetch_cover.return_value = None
        rm.return_value = 0
        imp.return_value = 0
        result = run_clean(
            library_root=root,
            cache_db=tmp_path / "mb.db",
            user_agent=("mint", "test", "x@y.z"),
        )

    from mint.tagger import read_track
    fixed = read_track(path)
    assert fixed.tpe1 == "Gorillaz"
    assert fixed.tpos == "1/1"
    assert result.applied >= 1
    rm.assert_called()
    imp.assert_called()
