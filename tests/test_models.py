from pathlib import Path

from mint.models import Track, TagDiff, Issue, MBTrack, MBRelease, IssueType


def test_track_holds_tag_values():
    t = Track(
        path=Path("/x.mp3"),
        tit2="Song", tpe1="A", tpe2="A", talb="Alb",
        tdrc="2020", trck="1/10", tpos="1/1", tcon="Rock",
        has_apic=True,
    )
    assert t.tit2 == "Song"
    assert t.has_apic is True


def test_tagdiff_carries_old_and_new():
    d = TagDiff(field="TPOS", current="", proposed="1/1")
    assert d.field == "TPOS"
    assert d.current == ""
    assert d.proposed == "1/1"


def test_issue_groups_diffs():
    diff = TagDiff(field="TPOS", current="", proposed="1/1")
    issue = Issue(
        path=Path("/x.mp3"),
        issue_type=IssueType.MISSING_TPOS,
        diffs=[diff],
    )
    assert issue.issue_type == IssueType.MISSING_TPOS
    assert len(issue.diffs) == 1


def test_mbrelease_track_lookup_by_disc_position():
    mb = MBRelease(
        release_id="rid",
        artist_credit_phrase="A",
        title="Alb",
        year="2020",
        tracks={
            (1, 1): MBTrack(disc=1, position=1, title="One", total_tracks=2, total_discs=1),
            (1, 2): MBTrack(disc=1, position=2, title="Two", total_tracks=2, total_discs=1),
        },
    )
    assert mb.tracks[(1, 1)].title == "One"
