from pathlib import Path

from mint.auditor import audit_track, propose_fixes, ProposedTags
from mint.models import Track, MBRelease, MBTrack, IssueType


def _mk_release(year="2005", title="Demon Days", artist="Gorillaz"):
    return MBRelease(
        release_id="rid-1",
        artist_credit_phrase=artist,
        title=title,
        year=year,
        tracks={
            (1, 6): MBTrack(disc=1, position=6, title="Feel Good Inc.",
                            total_tracks=15, total_discs=1),
        },
        candidate_release_ids=["rid-1"],
    )


def test_missing_tpos_flagged():
    t = Track(path=Path("/x.mp3"), tit2="Feel Good Inc.", tpe1="Gorillaz",
              tpe2="Gorillaz", talb="Demon Days", tdrc="2005",
              trck="6/15", tpos="", tcon="Alternative Rock", has_apic=True)
    issues = audit_track(t, _mk_release(), disc=1, position=6,
                         desired_genre="Alternative Rock")
    types = [i.issue_type for i in issues]
    assert IssueType.MISSING_TPOS in types


def test_tpe1_has_feat_flagged():
    t = Track(path=Path("/x.mp3"), tit2="Feel Good Inc.",
              tpe1="Gorillaz feat. De La Soul", tpe2="Gorillaz",
              talb="Demon Days", tdrc="2005", trck="6/15", tpos="1/1",
              tcon="Alternative Rock", has_apic=True)
    issues = audit_track(t, _mk_release(), disc=1, position=6,
                         desired_genre="Alternative Rock")
    types = [i.issue_type for i in issues]
    assert IssueType.TPE1_HAS_FEAT in types


def test_tpe1_ne_tpe2_flagged():
    t = Track(path=Path("/x.mp3"), tit2="Feel Good Inc.",
              tpe1="Different", tpe2="Gorillaz", talb="Demon Days",
              tdrc="2005", trck="6/15", tpos="1/1",
              tcon="Alternative Rock", has_apic=True)
    issues = audit_track(t, _mk_release(), disc=1, position=6,
                         desired_genre="Alternative Rock")
    types = [i.issue_type for i in issues]
    assert IssueType.TPE1_NE_TPE2 in types


def test_wrong_year_flagged():
    t = Track(path=Path("/x.mp3"), tit2="Feel Good Inc.", tpe1="Gorillaz",
              tpe2="Gorillaz", talb="Demon Days", tdrc="2010",
              trck="6/15", tpos="1/1", tcon="Alternative Rock", has_apic=True)
    issues = audit_track(t, _mk_release(), disc=1, position=6,
                         desired_genre="Alternative Rock")
    types = [i.issue_type for i in issues]
    assert IssueType.WRONG_YEAR in types


def test_missing_cover_flagged():
    t = Track(path=Path("/x.mp3"), tit2="Feel Good Inc.", tpe1="Gorillaz",
              tpe2="Gorillaz", talb="Demon Days", tdrc="2005",
              trck="6/15", tpos="1/1", tcon="Alternative Rock", has_apic=False)
    issues = audit_track(t, _mk_release(), disc=1, position=6,
                         desired_genre="Alternative Rock")
    types = [i.issue_type for i in issues]
    assert IssueType.MISSING_COVER in types


def test_clean_track_no_issues():
    t = Track(path=Path("/x.mp3"), tit2="Feel Good Inc.", tpe1="Gorillaz",
              tpe2="Gorillaz", talb="Demon Days", tdrc="2005",
              trck="6/15", tpos="1/1", tcon="Alternative Rock", has_apic=True)
    issues = audit_track(t, _mk_release(), disc=1, position=6,
                         desired_genre="Alternative Rock")
    assert issues == []


def test_propose_fixes_builds_full_tag_set():
    proposed = propose_fixes(
        mb_release=_mk_release(),
        disc=1, position=6,
        desired_genre="Alternative Rock",
    )
    assert proposed == ProposedTags(
        tit2="Feel Good Inc.",
        tpe1="Gorillaz",
        tpe2="Gorillaz",
        talb="Demon Days",
        tdrc="2005",
        trck="6/15",
        tpos="1/1",
        tcon="Alternative Rock",
    )
