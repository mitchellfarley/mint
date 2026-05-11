from mint.library import walk_library, build_dupe_index, normalize_for_dupe


def test_normalize_lowercases_and_strips_punctuation():
    assert normalize_for_dupe("Can't Hold Us") == "cant hold us"
    assert normalize_for_dupe("Feel Good Inc.") == "feel good inc"
    assert normalize_for_dupe("SICKO MODE") == "sicko mode"


def test_normalize_strips_feat_parens():
    assert normalize_for_dupe("Timeless (feat. Playboi Carti)") == "timeless"
    assert normalize_for_dupe("Song (ft. X)") == "song"
    assert normalize_for_dupe("Song [feat. X]") == "song"


def test_walk_library_finds_mp3s(tmp_path, make_mp3):
    root = tmp_path / "Music"
    artist = root / "Artist"
    album = artist / "Album"
    album.mkdir(parents=True)
    p1 = make_mp3(name=str(album / "01 Song.mp3"), tit2="Song")
    p2 = make_mp3(name=str(album / "02 Other.mp3"), tit2="Other")
    (album / "cover.jpg").write_bytes(b"x")
    found = sorted(walk_library(root))
    assert found == sorted([p1, p2])


def test_build_dupe_index_uses_artist_and_title(tmp_path, make_mp3):
    root = tmp_path / "Music"
    (root / "Artist" / "Album").mkdir(parents=True)
    make_mp3(name=str(root / "Artist" / "Album" / "01 A.mp3"),
             tit2="Song A", tpe1="Macklemore", tpe2="Macklemore")
    make_mp3(name=str(root / "Artist" / "Album" / "02 B.mp3"),
             tit2="Can't Hold Us", tpe1="Macklemore feat. Ray Dalton", tpe2="Macklemore")
    index = build_dupe_index(root)
    assert ("macklemore", "song a") in index
    assert ("macklemore", "cant hold us") in index
