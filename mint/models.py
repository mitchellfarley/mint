from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class IssueType(Enum):
    MISSING_TPOS = "MISSING_TPOS"
    TPE1_HAS_FEAT = "TPE1_HAS_FEAT"
    TPE1_NE_TPE2 = "TPE1_NE_TPE2"
    WRONG_YEAR = "WRONG_YEAR"
    WRONG_TITLE = "WRONG_TITLE"
    WRONG_ALBUM = "WRONG_ALBUM"
    WRONG_TRACK = "WRONG_TRACK"
    GENRE_INCONSISTENT = "GENRE_INCONSISTENT"
    MISSING_COVER = "MISSING_COVER"
    MB_LOOKUP_FAILED = "MB_LOOKUP_FAILED"


@dataclass
class Track:
    path: Path
    tit2: str = ""
    tpe1: str = ""
    tpe2: str = ""
    talb: str = ""
    tdrc: str = ""
    trck: str = ""
    tpos: str = ""
    tcon: str = ""
    has_apic: bool = False


@dataclass
class TagDiff:
    field: str
    current: str
    proposed: str


@dataclass
class Issue:
    path: Path
    issue_type: IssueType
    diffs: list[TagDiff] = field(default_factory=list)


@dataclass
class MBTrack:
    disc: int
    position: int
    title: str
    total_tracks: int
    total_discs: int


@dataclass
class MBRelease:
    release_id: str
    artist_credit_phrase: str
    title: str
    year: str
    tracks: dict[tuple[int, int], MBTrack] = field(default_factory=dict)
    candidate_release_ids: list[str] = field(default_factory=list)
