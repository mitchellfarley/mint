from mint.tagger import read_track


def test_read_track_returns_all_fields(make_mp3):
    path = make_mp3(
        tit2="Song", tpe1="A1", tpe2="A2", talb="Alb",
        tdrc="2020", trck="3/10", tpos="1/1", tcon="Rock",
    )
    t = read_track(path)
    assert t.path == path
    assert t.tit2 == "Song"
    assert t.tpe1 == "A1"
    assert t.tpe2 == "A2"
    assert t.talb == "Alb"
    assert t.tdrc == "2020"
    assert t.trck == "3/10"
    assert t.tpos == "1/1"
    assert t.tcon == "Rock"
    assert t.has_apic is False


def test_read_track_detects_cover_art(make_mp3):
    path = make_mp3(tit2="Song", apic=b"\xff\xd8\xff\xe0fake jpeg")
    t = read_track(path)
    assert t.has_apic is True


def test_read_track_missing_tags_are_empty(make_mp3):
    path = make_mp3(tit2="Just Title")
    t = read_track(path)
    assert t.tit2 == "Just Title"
    assert t.tpe1 == ""
    assert t.tpos == ""
