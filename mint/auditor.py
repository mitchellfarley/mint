from __future__ import annotations

import re
from dataclasses import dataclass

from mint.models import Issue, IssueType, MBRelease, TagDiff, Track


_FEAT_RE = re.compile(r"\b(?:feat\.?|ft\.?)\b", re.IGNORECASE)


@dataclass
class ProposedTags:
    tit2: str
    tpe1: str
    tpe2: str
    talb: str
    tdrc: str
    trck: str
    tpos: str
    tcon: str


def propose_fixes(
    mb_release: MBRelease,
    disc: int,
    position: int,
    desired_genre: str,
) -> ProposedTags:
    mbt = mb_release.tracks[(disc, position)]
    return ProposedTags(
        tit2=mbt.title,
        tpe1=mb_release.artist_credit_phrase,
        tpe2=mb_release.artist_credit_phrase,
        talb=mb_release.title,
        tdrc=mb_release.year,
        trck=f"{mbt.position}/{mbt.total_tracks}",
        tpos=f"{mbt.disc}/{mbt.total_discs}",
        tcon=desired_genre,
    )


def audit_track(
    track: Track,
    mb_release: MBRelease,
    disc: int,
    position: int,
    desired_genre: str,
) -> list[Issue]:
    proposed = propose_fixes(mb_release, disc, position, desired_genre)
    issues: list[Issue] = []

    if not track.tpos or track.tpos != proposed.tpos:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.MISSING_TPOS,
            diffs=[TagDiff("TPOS", track.tpos, proposed.tpos)],
        ))

    if _FEAT_RE.search(track.tpe1):
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.TPE1_HAS_FEAT,
            diffs=[TagDiff("TPE1", track.tpe1, proposed.tpe1)],
        ))
    elif track.tpe1 != proposed.tpe1:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.TPE1_NE_TPE2,
            diffs=[TagDiff("TPE1", track.tpe1, proposed.tpe1)],
        ))

    if track.tpe2 != proposed.tpe2:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.TPE1_NE_TPE2,
            diffs=[TagDiff("TPE2", track.tpe2, proposed.tpe2)],
        ))

    if track.tdrc != proposed.tdrc:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.WRONG_YEAR,
            diffs=[TagDiff("TDRC", track.tdrc, proposed.tdrc)],
        ))

    if track.tit2 != proposed.tit2:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.WRONG_TITLE,
            diffs=[TagDiff("TIT2", track.tit2, proposed.tit2)],
        ))

    if track.talb != proposed.talb:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.WRONG_ALBUM,
            diffs=[TagDiff("TALB", track.talb, proposed.talb)],
        ))

    if track.trck != proposed.trck:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.WRONG_TRACK,
            diffs=[TagDiff("TRCK", track.trck, proposed.trck)],
        ))

    if track.tcon != proposed.tcon:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.GENRE_INCONSISTENT,
            diffs=[TagDiff("TCON", track.tcon, proposed.tcon)],
        ))

    if not track.has_apic:
        issues.append(Issue(
            path=track.path,
            issue_type=IssueType.MISSING_COVER,
            diffs=[TagDiff("APIC", "(none)", "Cover Art Archive")],
        ))

    return issues
