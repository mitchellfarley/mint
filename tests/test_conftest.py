from mutagen.id3 import ID3


def test_mp3_fixture_factory_creates_readable_file(make_mp3):
    path = make_mp3(tit2="Test Song", tpe1="Test Artist")
    assert path.exists()
    tags = ID3(str(path))
    assert str(tags.get("TIT2")) == "Test Song"
    assert str(tags.get("TPE1")) == "Test Artist"


def test_mp3_fixture_factory_writes_all_fields(make_mp3):
    path = make_mp3(
        tit2="T", tpe1="A1", tpe2="A2", talb="Alb",
        tdrc="2020", trck="3/10", tpos="1/1", tcon="Rock",
    )
    tags = ID3(str(path))
    assert str(tags.get("TIT2")) == "T"
    assert str(tags.get("TPE1")) == "A1"
    assert str(tags.get("TPE2")) == "A2"
    assert str(tags.get("TALB")) == "Alb"
    assert str(tags.get("TDRC")) == "2020"
    assert str(tags.get("TRCK")) == "3/10"
    assert str(tags.get("TPOS")) == "1/1"
    assert str(tags.get("TCON")) == "Rock"
