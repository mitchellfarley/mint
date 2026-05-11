from mint.auditor import ProposedTags
from mint.fixer import apply_proposed
from mint.tagger import read_track


def test_apply_proposed_writes_all_fields(make_mp3):
    path = make_mp3(tit2="Old", tpe1="Old A", talb="Old Alb")
    proposed = ProposedTags(
        tit2="Feel Good Inc.",
        tpe1="Gorillaz",
        tpe2="Gorillaz",
        talb="Demon Days",
        tdrc="2005",
        trck="6/15",
        tpos="1/1",
        tcon="Alternative Rock",
    )
    apply_proposed(path, proposed, cover_data=b"\xff\xd8\xff\xe0fake" + b"\x00" * 100)
    t = read_track(path)
    assert t.tit2 == "Feel Good Inc."
    assert t.tpe1 == "Gorillaz"
    assert t.tpe2 == "Gorillaz"
    assert t.talb == "Demon Days"
    assert t.tdrc == "2005"
    assert t.trck == "6/15"
    assert t.tpos == "1/1"
    assert t.tcon == "Alternative Rock"
    assert t.has_apic is True


def test_apply_proposed_skips_cover_when_none(make_mp3):
    path = make_mp3(apic=b"\xff\xd8keep_this")
    proposed = ProposedTags(
        tit2="X", tpe1="A", tpe2="A", talb="B",
        tdrc="2000", trck="1/1", tpos="1/1", tcon="Rock",
    )
    apply_proposed(path, proposed, cover_data=None)
    t = read_track(path)
    assert t.has_apic is True
