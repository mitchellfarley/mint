from mint.title_parser import parse_title


def test_simple_dash_separator():
    p = parse_title("Radiohead - Karma Police")
    assert p is not None
    assert p.artist == "Radiohead"
    assert p.track == "Karma Police"


def test_strips_official_video_brackets():
    p = parse_title("Radiohead - Karma Police (Official Video)")
    assert p is not None
    assert p.artist == "Radiohead"
    assert p.track == "Karma Police"


def test_strips_lyrics_brackets():
    p = parse_title("Artist - Song [Lyrics]")
    assert p is not None
    assert p.track == "Song"


def test_preserves_feat_in_track():
    p = parse_title("Drake - Passionfruit feat. Some Guy (Official Audio)")
    assert p is not None
    assert p.artist == "Drake"
    assert "Passionfruit" in p.track
    assert "feat" in p.track.lower()


def test_em_dash_separator():
    p = parse_title("Artist — Song")
    assert p is not None
    assert p.artist == "Artist"
    assert p.track == "Song"


def test_pipe_separator():
    p = parse_title("Artist | Song")
    assert p is not None
    assert p.artist == "Artist"
    assert p.track == "Song"


def test_returns_none_when_no_separator():
    assert parse_title("Just a single string") is None


def test_returns_none_for_empty_string():
    assert parse_title("") is None


def test_preserves_non_noise_brackets():
    p = parse_title("Artist - Song (Remix)")
    assert p is not None
    assert "(Remix)" in p.track


def test_strips_4k_marker():
    p = parse_title("Artist - Song [4K]")
    assert p is not None
    assert p.track == "Song"
