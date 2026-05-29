from __future__ import annotations

import re
from dataclasses import dataclass


_NOISE_PATTERNS = [
    r"\bofficial\s+music\s+video\b",
    r"\bofficial\s+video\b",
    r"\bofficial\s+audio\b",
    r"\bofficial\s+lyric\s+video\b",
    r"\bofficial\s+visualizer\b",
    r"\blyric\s+video\b",
    r"\blyrics\b",
    r"\baudio\b",
    r"\bvisualizer\b",
    r"\bhd\b",
    r"\b4k\b",
    r"\bhq\b",
    r"\bremaster(?:ed)?\b",
    r"\bm/v\b",
    r"\bmv\b",
]
_NOISE_RE = re.compile("|".join(_NOISE_PATTERNS), re.IGNORECASE)
_BRACKETS_RE = re.compile(r"[\(\[\{][^\(\)\[\]\{\}]*[\)\]\}]")
_FEAT_RE = re.compile(r"\b(feat\.?|ft\.?|featuring)\s+[^\-\|]+", re.IGNORECASE)
_SEP_RE = re.compile(r"\s*[\-–—\|:]\s*")
_WS_RE = re.compile(r"\s+")


@dataclass
class ParsedTitle:
    artist: str
    track: str


def _strip_noise_brackets(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = _BRACKETS_RE.sub(
            lambda m: "" if _NOISE_RE.search(m.group(0)) else m.group(0),
            s,
        )
    return s


def _clean(s: str) -> str:
    s = s.strip().strip("\"'")
    s = _WS_RE.sub(" ", s)
    return s.strip()


def parse_title(video_title: str) -> ParsedTitle | None:
    if not video_title:
        return None
    s = _strip_noise_brackets(video_title)
    feat_match = _FEAT_RE.search(s)
    feat_suffix = ""
    if feat_match:
        feat_suffix = " " + feat_match.group(0).strip()
        s = s[: feat_match.start()] + s[feat_match.end():]

    parts = _SEP_RE.split(s, maxsplit=1)
    if len(parts) != 2:
        return None
    left, right = _clean(parts[0]), _clean(parts[1])
    if not left or not right:
        return None

    artist, track = left, right
    track = _clean(track + feat_suffix)
    return ParsedTitle(artist=artist, track=track)
