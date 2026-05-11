from mutagen.id3 import ID3

from mint.tagger import write_tags, write_cover, read_track


def test_write_tags_overwrites_all_fields(make_mp3):
    path = make_mp3(tit2="Old", tpe1="Old A", talb="Old Alb")
    write_tags(
        path,
        tit2="New Title",
        tpe1="New Artist",
        tpe2="New Artist",
        talb="New Album",
        tdrc="2021",
        trck="5/12",
        tpos="1/1",
        tcon="Indie Rock",
    )
    t = read_track(path)
    assert t.tit2 == "New Title"
    assert t.tpe1 == "New Artist"
    assert t.tpe2 == "New Artist"
    assert t.talb == "New Album"
    assert t.tdrc == "2021"
    assert t.trck == "5/12"
    assert t.tpos == "1/1"
    assert t.tcon == "Indie Rock"


def test_write_tags_saves_v23(make_mp3):
    path = make_mp3()
    write_tags(path, tit2="X")
    tags = ID3(str(path))
    assert tags.version[:2] == (2, 3)


def test_write_cover_embeds_apic(make_mp3):
    path = make_mp3()
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 200
    write_cover(path, jpeg)
    t = read_track(path)
    assert t.has_apic is True


def test_write_cover_replaces_existing_apic(make_mp3):
    path = make_mp3(apic=b"\xff\xd8\xff\xe0old")
    write_cover(path, b"\xff\xd8\xff\xe0new" + b"\x00" * 100)
    tags = ID3(str(path))
    apics = [tags[k] for k in tags.keys() if k.startswith("APIC")]
    assert len(apics) == 1
    assert apics[0].data.startswith(b"\xff\xd8\xff\xe0new")
