from mint.library import build_genre_index


def test_genre_index_picks_dominant_per_artist(tmp_path, make_mp3):
    root = tmp_path / "Music"
    (root / "Eagles" / "A").mkdir(parents=True)
    (root / "Eagles" / "B").mkdir(parents=True)
    make_mp3(name=str(root / "Eagles" / "A" / "01.mp3"),
             tpe1="Eagles", tpe2="Eagles", tit2="x", tcon="Classic Rock")
    make_mp3(name=str(root / "Eagles" / "A" / "02.mp3"),
             tpe1="Eagles", tpe2="Eagles", tit2="y", tcon="Classic Rock")
    make_mp3(name=str(root / "Eagles" / "B" / "01.mp3"),
             tpe1="Eagles", tpe2="Eagles", tit2="z", tcon="Rock")
    index = build_genre_index(root)
    assert index["eagles"] == "Classic Rock"


def test_genre_index_normalizes_artist_keys(tmp_path, make_mp3):
    root = tmp_path / "Music"
    (root / "RUFUS").mkdir(parents=True)
    make_mp3(name=str(root / "RUFUS" / "01.mp3"),
             tpe1="RÜFÜS DU SOL", tpe2="RÜFÜS DU SOL",
             tit2="a", tcon="Electronic")
    index = build_genre_index(root)
    # normalize_for_dupe lowercases but does NOT strip accents,
    # so the assertion uses the lowercased original.
    assert index["rüfüs du sol"] == "Electronic"


def test_genre_index_skips_tracks_without_tcon(tmp_path, make_mp3):
    root = tmp_path / "Music"
    (root / "A").mkdir(parents=True)
    make_mp3(name=str(root / "A" / "01.mp3"),
             tpe1="A", tpe2="A", tit2="x")  # no tcon
    make_mp3(name=str(root / "A" / "02.mp3"),
             tpe1="A", tpe2="A", tit2="y", tcon="Rock")
    index = build_genre_index(root)
    assert index["a"] == "Rock"


def test_genre_index_empty_library_returns_empty_dict(tmp_path):
    (tmp_path / "Music").mkdir()
    assert build_genre_index(tmp_path / "Music") == {}
