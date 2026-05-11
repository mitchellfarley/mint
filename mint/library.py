from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

from mint.tagger import read_track


_FEAT_PAREN_RE = re.compile(r"\s*[\(\[](?:feat\.?|ft\.?)[^)\]]*[\)\]]", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")
_FEAT_SUFFIX_RE = re.compile(r"\s+(?:feat\.?|ft\.?)\s+.+$", re.IGNORECASE)


def normalize_for_dupe(s: str) -> str:
    s = _FEAT_PAREN_RE.sub("", s)
    s = _FEAT_SUFFIX_RE.sub("", s)
    s = _PUNCT_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return s.lower()


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
