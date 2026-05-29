from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

from mint.tagger import read_track


_FEAT_PAREN_RE = re.compile(r"\s*[\(\[](?:feat\.?|ft\.?)[^)\]]*[\)\]]", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")
_FEAT_SUFFIX_RE = re.compile(r"\s+(?:feat\.?|ft\.?)\s+.+$", re.IGNORECASE)
_AMP_RE = re.compile(r"\s*(?:,|&|;|\bx\b|\band\b|\bvs\.?\b)\s*", re.IGNORECASE)


def normalize_for_dupe(s: str) -> str:
    s = _FEAT_PAREN_RE.sub("", s)
    s = _FEAT_SUFFIX_RE.sub("", s)
    s = _PUNCT_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return s.lower()


def strip_diacritics(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def primary_artist(s: str) -> str:
    s = _FEAT_PAREN_RE.sub("", s)
    s = _FEAT_SUFFIX_RE.sub("", s)
    s = _AMP_RE.split(s, maxsplit=1)[0]
    return s.strip()


def normalize_for_mb_search(s: str) -> str:
    s = strip_diacritics(s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def normalize_artist_for_mb(s: str) -> str:
    return normalize_for_mb_search(primary_artist(s))


def normalize_title_for_mb(s: str) -> str:
    s = _FEAT_PAREN_RE.sub("", s)
    s = _FEAT_SUFFIX_RE.sub("", s)
    return normalize_for_mb_search(s)


def walk_library(root: Path) -> Iterator[Path]:
    yield from sorted(root.rglob("*.mp3"))


def build_dupe_index(root: Path) -> set[tuple[str, str]]:
    index: set[tuple[str, str]] = set()
    for path in walk_library(root):
        t = read_track(path)
        artist = t.tpe2 or t.tpe1
        if not artist or not t.tit2:
            continue
        index.add((normalize_for_dupe(artist), normalize_for_dupe(t.tit2)))
    return index


def build_genre_index(root: Path) -> dict[str, str]:
    """Return {normalized_artist: dominant_genre} from the existing library.

    For each artist, the dominant genre is the TCON value used by the most
    tracks. Tracks without TCON are ignored.
    """
    counts: dict[str, Counter] = defaultdict(Counter)
    for path in walk_library(root):
        t = read_track(path)
        artist = t.tpe2 or t.tpe1
        if not artist or not t.tcon:
            continue
        counts[normalize_for_dupe(artist)][t.tcon] += 1
    return {a: c.most_common(1)[0][0] for a, c in counts.items()}
