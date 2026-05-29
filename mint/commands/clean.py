from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from mint.auditor import audit_track, propose_fixes
from mint.cleaner import apply_proposed
from mint.itunes import import_file, remove_album
from mint.library import build_genre_index, normalize_for_dupe, walk_library
from mint.mb_cache import MBCache
from mint.mb_client import MBClient
from mint.reporter import format_report
from mint.tagger import read_track


@dataclass
class CleanResult:
    applied: int = 0
    aborted: bool = False


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _progress(idx: int, total: int, label: str, status: str) -> None:
    width = len(str(total))
    line = f"[{idx:>{width}}/{total}] {_truncate(label, 50):<50} {status}"
    sys.stdout.write("\r\x1b[2K" + line)
    sys.stdout.flush()


def _progress_done(idx: int, total: int, label: str, status: str) -> None:
    _progress(idx, total, label, status)
    sys.stdout.write("\n")
    sys.stdout.flush()


def run_clean(
    library_root: Path,
    cache_db: Path,
    user_agent: tuple[str, str, str],
) -> CleanResult:
    cache = MBCache(cache_db)
    client = MBClient(cache=cache, user_agent=user_agent)

    print("Scanning library...", end="", flush=True)
    paths = list(walk_library(library_root))
    tracks = [read_track(p) for p in paths]
    print(f" {len(tracks)} tracks", flush=True)

    by_album: dict[tuple[str, str], list] = defaultdict(list)
    for t in tracks:
        by_album[(t.tpe2 or t.tpe1, t.talb)].append(t)

    print("Building genre index...", flush=True)
    genre_index = build_genre_index(library_root)

    albums = list(by_album.items())
    total = len(albums)
    print(f"Auditing {total} albums...", flush=True)

    issues = []
    clean_plan: list[tuple[Path, "ProposedTags", str]] = []
    matched = 0
    no_match = 0
    no_metadata = 0

    for idx, ((artist, album), album_tracks) in enumerate(albums, start=1):
        label = f"{artist or '?'} — {album or '?'}"
        if not artist or not album:
            no_metadata += 1
            _progress_done(idx, total, label, "skipped (missing artist/album)")
            continue

        _progress(idx, total, label, "looking up...")
        mb_release = client.lookup_release(artist, album)
        if mb_release is None:
            no_match += 1
            _progress_done(idx, total, label, "no MB match")
            continue

        track_issues_count = 0
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
                track_issues_count += 1
                proposed = propose_fixes(mb_release, disc=match[0],
                                          position=match[1], desired_genre=genre)
                clean_plan.append((t.path, proposed, mb_release.title))

        matched += 1
        status = "clean" if track_issues_count == 0 else f"{track_issues_count} issue(s)"
        _progress_done(idx, total, label, status)

    print()
    print(f"Audit summary: {matched} matched, {no_match} no MB match, "
          f"{no_metadata} missing tags")
    print()
    print(format_report(issues, scanned=len(tracks)))
    if not clean_plan:
        return CleanResult(applied=0)

    prompt = f"Apply these {len(clean_plan)} changes? [y/N] "
    print(prompt, end="", flush=True)
    answer = input("").strip().lower()
    if answer != "y":
        print("Aborted, no changes written.")
        return CleanResult(applied=0, aborted=True)

    affected_albums: set[str] = set()
    plan_total = len(clean_plan)
    for idx, (path, proposed, album_title) in enumerate(clean_plan, start=1):
        _progress(idx, plan_total, proposed.tit2, "writing tags")
        apply_proposed(path, proposed, cover_data=None)
        affected_albums.add(album_title)
    sys.stdout.write("\n")

    print(f"Re-importing {len(affected_albums)} affected album(s)...")
    for album_title in affected_albums:
        remove_album(album_title)
    import_total = len(clean_plan)
    for idx, (path, proposed, _) in enumerate(clean_plan, start=1):
        _progress(idx, import_total, proposed.tit2, "importing")
        import_file(str(path))
    sys.stdout.write("\n")

    print(f"Applied {len(clean_plan)} changes, re-imported {len(affected_albums)} albums.")
    return CleanResult(applied=len(clean_plan))
