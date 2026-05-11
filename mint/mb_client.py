from __future__ import annotations

import time
import unicodedata
from typing import Iterable

import musicbrainzngs
import requests

from mint.mb_cache import MBCache
from mint.models import MBRelease, MBTrack


COVER_ART_URL = "https://coverartarchive.org/release/{rid}/front"
RATE_LIMIT_SECONDS = 0.4


def cache_key(artist: str, album: str) -> str:
    def norm(s: str) -> str:
        s = unicodedata.normalize("NFKC", s)
        return s.lower().strip()
    return f"{norm(artist)}::{norm(album)}"


def _release_sort_key(release: dict) -> tuple:
    date = release.get("date") or "9999"
    country = release.get("country") or ""
    country_priority = 0 if country in ("US", "XW", "") else 1
    return (date, country_priority)


def _build_mb_release(detail: dict, candidates: list[str]) -> MBRelease:
    rel = detail["release"]
    year = (rel.get("date") or "")[:4]
    tracks: dict[tuple[int, int], MBTrack] = {}
    media = rel.get("medium-list", [])
    total_discs = len(media)
    for medium in media:
        disc = int(medium.get("position", 1))
        total_tracks = int(medium.get("track-count", 0))
        for trk in medium.get("track-list", []):
            pos = int(trk.get("position", 0))
            title = trk.get("recording", {}).get("title", "")
            tracks[(disc, pos)] = MBTrack(
                disc=disc,
                position=pos,
                title=title,
                total_tracks=total_tracks,
                total_discs=total_discs,
            )
    return MBRelease(
        release_id=rel["id"],
        artist_credit_phrase=rel.get("artist-credit-phrase", ""),
        title=rel.get("title", ""),
        year=year,
        tracks=tracks,
        candidate_release_ids=candidates,
    )


class MBClient:
    def __init__(self, cache: MBCache, user_agent: tuple[str, str, str] | None = None) -> None:
        self.cache = cache
        if user_agent:
            musicbrainzngs.set_useragent(*user_agent)
        self._last_call = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)
        self._last_call = time.monotonic()

    def lookup_release(self, artist: str, album: str) -> MBRelease | None:
        key = cache_key(artist, album)
        cached = self.cache.get(key)
        if cached is not None:
            return _build_mb_release(cached["detail"], cached["candidates"])

        self._throttle()
        results = musicbrainzngs.search_releases(artist=artist, release=album, limit=5)
        candidates_raw = results.get("release-list", [])
        official = [r for r in candidates_raw if r.get("status") == "Official"]
        pool = official or candidates_raw
        if not pool:
            return None
        pool_sorted = sorted(pool, key=_release_sort_key)
        candidate_ids = [r["id"] for r in pool_sorted]

        self._throttle()
        detail = musicbrainzngs.get_release_by_id(
            candidate_ids[0],
            includes=["recordings", "artist-credits"],
        )
        self.cache.set(key, {"detail": detail, "candidates": candidate_ids})
        return _build_mb_release(detail, candidate_ids)

    def fetch_cover(self, release_ids: Iterable[str]) -> bytes | None:
        for rid in release_ids:
            cached = self.cache.get_cover(rid)
            if cached is not None:
                return cached
            try:
                r = requests.get(COVER_ART_URL.format(rid=rid), timeout=15, allow_redirects=True)
            except requests.RequestException:
                continue
            if r.status_code == 200:
                self.cache.set_cover(rid, r.content)
                return r.content
        return None
