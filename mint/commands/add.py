from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mint.auditor import propose_fixes
from mint.cleaner import apply_proposed
from mint.downloader import download_url
from mint.itunes import import_file
from mint.library import (
    build_dupe_index,
    build_genre_index,
    normalize_artist_for_mb,
    normalize_for_dupe,
    normalize_title_for_mb,
)
from mint.mb_cache import MBCache
from mint.mb_client import MBClient
from mint.mover import destination_path, move_to_library
from mint.progress import progress, progress_done
from mint.tagger import read_track
from mint.title_parser import parse_title


@dataclass
class AddSummary:
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    failed_titles: list[str] = field(default_factory=list)


def run_add(
    youtube_url: str,
    library_root: Path,
    staging_dir: Path,
    cache_db: Path,
    user_agent: tuple[str, str, str],
) -> AddSummary:
    summary = AddSummary()
    staging_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading from YouTube...", flush=True)
    downloaded = download_url(youtube_url, staging_dir)
    if not downloaded:
        print("No audio downloaded.")
        return summary
    print(f"Downloaded {len(downloaded)} track(s)", flush=True)

    print("Indexing existing library...", flush=True)
    dupe_index = build_dupe_index(library_root) if library_root.exists() else set()
    genre_index = build_genre_index(library_root) if library_root.exists() else {}
    cache = MBCache(cache_db)
    client = MBClient(cache=cache, user_agent=user_agent)

    total = len(downloaded)
    for idx, d in enumerate(downloaded, start=1):
        path = d.path
        artist = ""
        title = ""

        if d.artist and d.track:
            artist, title = d.artist, d.track
        else:
            parsed = parse_title(d.title)
            if parsed is not None:
                artist, title = parsed.artist, parsed.track
            elif d.uploader:
                artist, title = d.uploader, d.title

        if not artist or not title:
            summary.failed += 1
            summary.failed_titles.append(d.title or path.name)
            progress_done(idx, total, d.title or path.name, "unparseable title")
            continue

        label = f"{artist} — {title}"

        if (normalize_for_dupe(artist), normalize_for_dupe(title)) in dupe_index:
            path.unlink(missing_ok=True)
            summary.skipped += 1
            progress_done(idx, total, label, "duplicate, skipped")
            continue

        mb_artist = normalize_artist_for_mb(artist)
        mb_title = normalize_title_for_mb(title)
        progress(idx, total, label, "looking up MusicBrainz...")
        lookup = client.lookup_recording(mb_artist, mb_title)
        if lookup is None:
            summary.failed += 1
            summary.failed_titles.append(title)
            progress_done(idx, total, label, "no MB match")
            continue

        mb_release, disc, position = lookup
        if (disc, position) not in mb_release.tracks:
            summary.failed += 1
            summary.failed_titles.append(title)
            progress_done(idx, total, label, "track not in release")
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

        progress(idx, total, label, "fetching cover art..." if not has_cover else "writing tags...")
        cover = client.fetch_cover(mb_release.candidate_release_ids) if not has_cover else None

        progress(idx, total, label, "writing tags...")
        apply_proposed(path, proposed, cover_data=cover)

        dst = destination_path(library_root, proposed.tpe2, proposed.talb,
                                int(proposed.trck.split("/")[0]), proposed.tit2)
        progress(idx, total, label, "moving to library...")
        move_to_library(path, dst)

        progress(idx, total, label, "importing to Apple Music...")
        import_file(str(dst))

        summary.imported += 1
        progress_done(idx, total, label, f"imported as {proposed.tit2}")

    return summary
