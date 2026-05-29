from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mint.auditor import propose_fixes
from mint.downloader import download_url
from mint.cleaner import apply_proposed
from mint.itunes import import_file
from mint.library import build_dupe_index, build_genre_index, normalize_for_dupe
from mint.mb_cache import MBCache
from mint.mb_client import MBClient
from mint.mover import destination_path, move_to_library
from mint.tagger import read_track
from mint.title_parser import parse_title


@dataclass
class AddSummary:
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    failed_titles: list[str] = field(default_factory=list)


def _print_step(idx: int, total: int, label: str, title: str, result: str) -> None:
    print(f"[{idx}/{total}] {label:<11} {title[:40]:<40}  {result}")


def run_add(
    youtube_url: str,
    library_root: Path,
    staging_dir: Path,
    cache_db: Path,
    user_agent: tuple[str, str, str],
) -> AddSummary:
    summary = AddSummary()
    staging_dir.mkdir(parents=True, exist_ok=True)

    downloaded = download_url(youtube_url, staging_dir)
    if not downloaded:
        return summary

    dupe_index = build_dupe_index(library_root) if library_root.exists() else set()
    genre_index = build_genre_index(library_root) if library_root.exists() else {}
    cache = MBCache(cache_db)
    client = MBClient(cache=cache, user_agent=user_agent)

    total = len(downloaded)
    for idx, (path, video_title) in enumerate(downloaded, start=1):
        parsed = parse_title(video_title)
        if parsed is None:
            summary.failed += 1
            summary.failed_titles.append(video_title or path.name)
            _print_step(idx, total, "failed", video_title or path.name, "unparseable title")
            continue

        artist, title = parsed.artist, parsed.track

        if (normalize_for_dupe(artist), normalize_for_dupe(title)) in dupe_index:
            path.unlink(missing_ok=True)
            summary.skipped += 1
            _print_step(idx, total, "duplicate", title, "skipped")
            continue

        lookup = client.lookup_recording(artist, title)
        if lookup is None:
            summary.failed += 1
            summary.failed_titles.append(title)
            _print_step(idx, total, "failed", title, "no MB match")
            continue

        mb_release, disc, position = lookup
        if (disc, position) not in mb_release.tracks:
            summary.failed += 1
            summary.failed_titles.append(title)
            _print_step(idx, total, "failed", title, "track not in release")
            continue

        try:
            track = read_track(path)
        except Exception:
            track = None
        existing_genre = track.tcon if track else ""
        has_cover = track.has_apic if track else False

        artist_key = normalize_for_dupe(mb_release.artist_credit_phrase)
        genre = genre_index.get(artist_key) or existing_genre or ""
        proposed = propose_fixes(mb_release, disc=disc, position=position,
                                  desired_genre=genre)
        cover = client.fetch_cover(mb_release.candidate_release_ids) if not has_cover else None
        apply_proposed(path, proposed, cover_data=cover)

        dst = destination_path(library_root, proposed.tpe2, proposed.talb,
                                int(proposed.trck.split("/")[0]), proposed.tit2)
        move_to_library(path, dst)
        import_file(str(dst))

        summary.imported += 1
        _print_step(idx, total, "imported", proposed.tit2, "done")

    return summary
