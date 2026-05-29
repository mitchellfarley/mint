from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from mint.itunes import remove_track
from mint.library import normalize_for_dupe, walk_library
from mint.tagger import read_track


_THE_PREFIX = re.compile(r"^the\s+", re.IGNORECASE)


def _normalize_artist(s: str) -> str:
    s = _THE_PREFIX.sub("", s.strip())
    return normalize_for_dupe(s)


@dataclass
class DupResult:
    track_groups: dict[tuple[str, str], list[Path]] = field(default_factory=dict)
    album_groups: dict[tuple[str, str], list[Path]] = field(default_factory=dict)
    artist_groups: dict[str, list[str]] = field(default_factory=dict)
    removed: int = 0
    aborted: bool = False


def run_dup(library_root: Path) -> DupResult:
    print(f"Scanning {library_root}...", flush=True)
    paths = list(walk_library(library_root))
    print(f"  {len(paths)} tracks", flush=True)

    tracks_by_key: dict[tuple[str, str], list[Path]] = defaultdict(list)
    albums_by_key: dict[tuple[str, str], set] = defaultdict(set)
    artists_by_key: dict[str, set[str]] = defaultdict(set)
    artist_display: dict[str, str] = {}

    for p in paths:
        try:
            t = read_track(p)
        except Exception:
            continue
        artist = t.tpe2 or t.tpe1
        title = t.tit2
        album = t.talb
        if not artist:
            continue

        a_key = _normalize_artist(artist)
        artists_by_key[a_key].add(artist)
        artist_display.setdefault(a_key, artist)

        if album:
            albums_by_key[(a_key, normalize_for_dupe(album))].add(p.parent)

        if title:
            tracks_by_key[(a_key, normalize_for_dupe(title))].append(p)

    track_dupes = {k: v for k, v in tracks_by_key.items() if len(v) > 1}
    album_dupes = {k: sorted(v) for k, v in albums_by_key.items() if len(v) > 1}
    artist_dupes = {k: sorted(v) for k, v in artists_by_key.items() if len(v) > 1}

    result = DupResult(
        track_groups=track_dupes,
        album_groups=album_dupes,
        artist_groups=artist_dupes,
    )

    if not track_dupes and not album_dupes and not artist_dupes:
        print("No duplicates found.")
        return result

    if artist_dupes:
        print()
        print(f"Duplicate artists ({len(artist_dupes)} group(s)):")
        for key, variants in sorted(artist_dupes.items()):
            print(f"  {artist_display[key]}")
            for v in variants:
                print(f"    {v}")
        print("  (manual rename/merge required)")

    if album_dupes:
        print()
        print(f"Duplicate albums ({len(album_dupes)} group(s)):")
        for (a_key, _), dirs in sorted(album_dupes.items()):
            print(f"  {artist_display.get(a_key, a_key)} — {dirs[0].name}")
            for d in dirs:
                print(f"    {d}")
        print("  (manual merge required)")

    if track_dupes:
        total_extra = sum(len(v) - 1 for v in track_dupes.values())
        print()
        print(f"Duplicate tracks ({len(track_dupes)} group(s), {total_extra} extra file(s)):")
        for (a_key, _), files in sorted(track_dupes.items()):
            first = read_track(files[0])
            print(f"  {first.tpe2 or first.tpe1} — {first.tit2}")
            for i, f in enumerate(files):
                marker = "keep" if i == 0 else "delete"
                print(f"    [{marker}] {f}")

        print()
        prompt = f"Delete {total_extra} extra track file(s)? [y/N] "
        print(prompt, end="", flush=True)
        answer = input("").strip().lower()
        if answer != "y":
            print("Aborted, no files removed.")
            result.aborted = True
            return result

        removed = 0
        for files in track_dupes.values():
            keep = files[0]
            for victim in files[1:]:
                try:
                    t = read_track(victim)
                except Exception:
                    t = None
                victim.unlink(missing_ok=True)
                if t and t.tit2:
                    remove_track(t.tit2, t.tpe1 or t.tpe2 or "")
                removed += 1
        result.removed = removed
        print(f"Removed {removed} duplicate track file(s).")

    return result
