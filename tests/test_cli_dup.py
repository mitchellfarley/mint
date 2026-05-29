from mint.commands.dup import _normalize_artist, run_dup


def test_normalize_artist_strips_the():
    assert _normalize_artist("The Offspring") == _normalize_artist("Offspring")


def test_normalize_artist_case_insensitive():
    assert _normalize_artist("Radiohead") == _normalize_artist("RADIOHEAD")


def test_run_dup_finds_track_duplicates(tmp_path, make_mp3, capsys, monkeypatch):
    root = tmp_path / "Library"
    (root / "Gorillaz" / "Demon Days").mkdir(parents=True)
    (root / "Gorillaz" / "Greatest Hits").mkdir(parents=True)

    make_mp3(name=str(root / "Gorillaz" / "Demon Days" / "06 Feel Good Inc..mp3"),
             tit2="Feel Good Inc.", tpe1="Gorillaz", tpe2="Gorillaz",
             talb="Demon Days")
    make_mp3(name=str(root / "Gorillaz" / "Greatest Hits" / "03 Feel Good Inc..mp3"),
             tit2="Feel Good Inc.", tpe1="Gorillaz", tpe2="Gorillaz",
             talb="Greatest Hits")
    monkeypatch.setattr("builtins.input", lambda _: "n")

    result = run_dup(library_root=root)

    assert len(result.track_groups) == 1
    assert result.aborted is True
    out = capsys.readouterr().out
    assert "Duplicate tracks" in out
    assert "Feel Good Inc." in out


def test_run_dup_deletes_extras_on_confirm(tmp_path, make_mp3, monkeypatch):
    root = tmp_path / "Library"
    (root / "Gorillaz" / "Demon Days").mkdir(parents=True)
    (root / "Gorillaz" / "Greatest Hits").mkdir(parents=True)

    keep = make_mp3(name=str(root / "Gorillaz" / "Demon Days" / "06 Feel Good Inc..mp3"),
                    tit2="Feel Good Inc.", tpe1="Gorillaz", tpe2="Gorillaz",
                    talb="Demon Days")
    extra = make_mp3(name=str(root / "Gorillaz" / "Greatest Hits" / "03 Feel Good Inc..mp3"),
                     tit2="Feel Good Inc.", tpe1="Gorillaz", tpe2="Gorillaz",
                     talb="Greatest Hits")
    monkeypatch.setattr("builtins.input", lambda _: "y")
    monkeypatch.setattr("mint.commands.dup.remove_track", lambda title, artist: 0)

    result = run_dup(library_root=root)

    assert result.removed == 1
    assert keep.exists()
    assert not extra.exists()


def test_run_dup_finds_artist_duplicates(tmp_path, make_mp3, capsys):
    root = tmp_path / "Library"
    (root / "Offspring" / "Smash").mkdir(parents=True)
    (root / "The Offspring" / "Americana").mkdir(parents=True)

    make_mp3(name=str(root / "Offspring" / "Smash" / "01 Come Out and Play.mp3"),
             tit2="Come Out and Play", tpe1="Offspring", tpe2="Offspring",
             talb="Smash")
    make_mp3(name=str(root / "The Offspring" / "Americana" / "01 Pretty Fly.mp3"),
             tit2="Pretty Fly", tpe1="The Offspring", tpe2="The Offspring",
             talb="Americana")

    result = run_dup(library_root=root)

    assert len(result.artist_groups) == 1
    out = capsys.readouterr().out
    assert "Duplicate artists" in out


def test_run_dup_finds_album_duplicates(tmp_path, make_mp3, capsys):
    root = tmp_path / "Library"
    (root / "Gorillaz" / "Demon Days").mkdir(parents=True)
    (root / "Gorillaz" / "Demon Days (Deluxe)").mkdir(parents=True)

    make_mp3(name=str(root / "Gorillaz" / "Demon Days" / "01 Intro.mp3"),
             tit2="Intro", tpe1="Gorillaz", tpe2="Gorillaz", talb="Demon Days")
    make_mp3(name=str(root / "Gorillaz" / "Demon Days (Deluxe)" / "01 Intro 2.mp3"),
             tit2="Intro 2", tpe1="Gorillaz", tpe2="Gorillaz", talb="Demon Days")

    result = run_dup(library_root=root)

    assert len(result.album_groups) == 1
    out = capsys.readouterr().out
    assert "Duplicate albums" in out


def test_run_dup_no_duplicates(tmp_path, make_mp3, capsys):
    root = tmp_path / "Library"
    (root / "Radiohead" / "OK Computer").mkdir(parents=True)
    make_mp3(name=str(root / "Radiohead" / "OK Computer" / "06 Karma Police.mp3"),
             tit2="Karma Police", tpe1="Radiohead", tpe2="Radiohead",
             talb="OK Computer")

    result = run_dup(library_root=root)

    assert len(result.track_groups) == 0
    assert len(result.album_groups) == 0
    assert len(result.artist_groups) == 0
    out = capsys.readouterr().out
    assert "No duplicates" in out
