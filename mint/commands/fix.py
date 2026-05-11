from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from mint.auditor import audit_track, propose_fixes
from mint.fixer import apply_proposed
from mint.itunes import import_file, remove_album
from mint.library import build_genre_index, normalize_for_dupe, walk_library
from mint.mb_cache import MBCache
from mint.mb_client import MBClient
from mint.reporter import format_report
from mint.tagger import read_track


@dataclass
class FixResult:
    applied: int = 0
    aborted: bool = False


def run_fix(
    library_root: Path,
    cache_db: Path,
    user_agent: tuple[str, str, str],
) -> FixResult:
    cache = MBCache(cache_db)
    client = MBClient(cache=cache, user_agent=user_agent)

    tracks = [read_track(p) for p in walk_library(library_root)]
    by_album: dict[tuple[str, str], list] = defaultdict(list)
    for t in tracks:
        by_album[(t.tpe2 or t.tpe1, t.talb)].append(t)

    genre_index = build_genre_index(library_root)

    issues = []
    fix_plan: list[tuple[Path, "ProposedTags", str]] = []
    for (artist, album), album_tracks in by_album.items():
        if not artist or not album:
            continue
        mb_release = client.lookup_release(artist, album)
        if mb_release is None:
            continue
        for t in album_tracks:
            match = None
            for key, mbt in mb_release.tracks.items():
                if normalize_for_dupe(mbt.title) == normalize_for_dupe(t.tit2):
                    match = key
                    break
            if match is None:
                continue
            artist_key = normalize_for_dupe(mb_release.artist_credit_phrase)
            genre = genre_index.get(artist_key) or t.tcon or ""
            t_issues = audit_track(t, mb_release, disc=match[0],
                                    position=match[1], desired_genre=genre)
            if t_issues:
                issues.extend(t_issues)
                proposed = propose_fixes(mb_release, disc=match[0],
                                          position=match[1], desired_genre=genre)
                fix_plan.append((t.path, proposed, mb_release.title))

    print(format_report(issues, scanned=len(tracks)))
    if not fix_plan:
        return FixResult(applied=0)

    prompt = f"Apply these {len(fix_plan)} changes? [y/N] "
    print(prompt, end="", flush=True)
    answer = input("").strip().lower()
    if answer != "y":
        print("Aborted, no changes written.")
        return FixResult(applied=0, aborted=True)

    affected_albums: set[str] = set()
    for path, proposed, album_title in fix_plan:
        apply_proposed(path, proposed, cover_data=None)
        affected_albums.add(album_title)

    for album_title in affected_albums:
        remove_album(album_title)
    for path, proposed, _ in fix_plan:
        import_file(str(path))

    print(f"Applied {len(fix_plan)} changes, re-imported {len(affected_albums)} albums.")
    return FixResult(applied=len(fix_plan))
