from __future__ import annotations

import re
import time
import unicodedata
from typing import Callable, Iterable

import musicbrainzngs
import requests

from mint.library import normalize_for_dupe
from mint.mb_cache import MBCache
from mint.models import MBRelease, MBTrack


COVER_ART_URL = "https://coverartarchive.org/release/{rid}/front"
RATE_LIMIT_SECONDS = 0.4

_WS_RE = re.compile(r"\s+")


def cache_key(artist: str, album: str) -> str:
    def norm(s: str) -> str:
        s = unicodedata.normalize("NFKD", s).encode("ascii", errors="ignore").decode("ascii")
        return _WS_RE.sub(" ", s.lower()).strip()
    return f"{norm(artist)}::{norm(album)}"


def _release_sort_key(release: dict) -> tuple:
    quality = _release_quality(release)
    date = release.get("date") or "9999"
    country = release.get("country") or ""
    country_priority = 0 if country in ("US", "XW", "") else 1
    return (quality, date, country_priority)


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


_BAD_SECONDARY_TYPES = {
    "mixtape/street", "compilation", "dj-mix", "demo", "bootleg",
    "interview", "spokenword", "audiobook", "soundtrack", "karaoke",
}
_DEMOTED_SECONDARY_TYPES = {
    "live", "remix",
}


def _release_quality(release: dict) -> int:
    """Lower is better. 0 = canonical studio album, higher = less canonical."""
    rg = release.get("release-group", {}) or {}
    primary = (rg.get("primary-type") or "").lower()
    secondaries = {s.lower() for s in (rg.get("secondary-type-list") or [])}
    if secondaries & _BAD_SECONDARY_TYPES:
        return 100
    demoted = bool(secondaries & _DEMOTED_SECONDARY_TYPES)
    if primary == "album":
        return 30 if demoted else 0
    if primary == "ep":
        return 40 if demoted else 10
    if primary == "single":
        return 50 if demoted else 20
    return 60


def _pick_release_id_from_recording(recording: dict) -> str | None:
    best = _best_release_for_recording(recording)
    return best["id"] if best is not None else None


def _best_release_for_recording(recording: dict) -> dict | None:
    rel_list = recording.get("release-list", [])
    if not rel_list:
        return None
    official = [r for r in rel_list if r.get("status") == "Official"]
    pool = official or rel_list
    pool_sorted = sorted(pool, key=_release_sort_key)
    chosen = pool_sorted[0]
    if _release_quality(chosen) >= 100:
        return None
    return chosen


def _candidate_summary(recording: dict, release: dict) -> dict:
    rg = release.get("release-group", {}) or {}
    primary = rg.get("primary-type") or ""
    return {
        "recording_id": recording.get("id"),
        "recording_title": recording.get("title", ""),
        "release_id": release.get("id"),
        "artist": (
            recording.get("artist-credit-phrase")
            or release.get("artist-credit-phrase")
            or ""
        ),
        "title": release.get("title", ""),
        "year": (release.get("date") or "")[:4],
        "type": primary,
        "country": release.get("country") or "",
        "quality": _release_quality(release),
    }


def _find_position_in_detail(detail: dict, recording_id: str) -> tuple[int, int] | None:
    rel = detail["release"]
    for medium in rel.get("medium-list", []):
        disc = int(medium.get("position", 1))
        for trk in medium.get("track-list", []):
            if trk.get("recording", {}).get("id") == recording_id:
                return disc, int(trk.get("position", 0))
    return None


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

    def _full_releases_for_recording(self, recording_id: str) -> list[dict]:
        cache_k = f"recrel::{recording_id}"
        cached = self.cache.get(cache_k)
        if cached is not None:
            return cached.get("releases", [])
        self._throttle()
        try:
            result = musicbrainzngs.browse_releases(
                recording=recording_id,
                includes=["release-groups"],
                limit=100,
            )
        except Exception:
            return []
        releases = result.get("release-list", [])
        self.cache.set(cache_k, {"releases": releases})
        return releases

    def _best_release_from_full_list(self, releases: list[dict]) -> dict | None:
        if not releases:
            return None
        official = [r for r in releases if r.get("status") == "Official"]
        pool = official or releases
        pool_sorted = sorted(pool, key=_release_sort_key)
        chosen = pool_sorted[0]
        if _release_quality(chosen) >= 100:
            return None
        return chosen

    def lookup_recording(
        self,
        artist: str,
        title: str,
        prompter: Callable[[list[dict]], int | None] | None = None,
    ) -> tuple[MBRelease, int, int] | None:
        rec_key = f"rec::{cache_key(artist, title)}"
        cached = self.cache.get(rec_key)
        if cached is not None and "recording_id" in cached and "release_id" in cached:
            release_id = cached["release_id"]
            recording_id = cached["recording_id"]
        else:
            self._throttle()
            results = musicbrainzngs.search_recordings(
                artist=artist, recording=title, limit=25
            )
            recordings = results.get("recording-list", [])
            if not recordings:
                return None

            query_norm = normalize_for_dupe(title)
            matched_recordings = [
                rec for rec in recordings
                if normalize_for_dupe(rec.get("title", "")) == query_norm
            ]
            recordings_to_evaluate = matched_recordings or recordings

            candidates: list[dict] = []
            for rec in recordings_to_evaluate:
                rec_id = rec.get("id")
                if not rec_id:
                    continue
                full_releases = self._full_releases_for_recording(rec_id)
                if full_releases:
                    best = self._best_release_from_full_list(full_releases)
                else:
                    best = _best_release_for_recording(rec)
                if best is None:
                    continue
                candidates.append(_candidate_summary(rec, best))

            if not candidates:
                return None

            candidates.sort(
                key=lambda c: (c.get("quality", 0), c.get("year") or "9999")
            )

            chosen_idx = 0
            if prompter is not None and len(candidates) > 1:
                top = candidates[:3]
                base_q = top[0]["quality"]
                if any(c["quality"] - base_q <= 10 for c in top[1:]):
                    picked = prompter(top)
                    if picked is None:
                        return None
                    chosen_idx = picked
            chosen = candidates[chosen_idx]
            release_id = chosen["release_id"]
            recording_id = chosen["recording_id"]
            self.cache.set(rec_key, {
                "release_id": release_id,
                "recording_id": recording_id,
            })

        release_key = f"rid::{release_id}"
        cached_rel = self.cache.get(release_key)
        if cached_rel is not None:
            detail = cached_rel["detail"]
        else:
            self._throttle()
            detail = musicbrainzngs.get_release_by_id(
                release_id,
                includes=["recordings", "artist-credits"],
            )
            self.cache.set(release_key, {"detail": detail, "candidates": [release_id]})

        pos = _find_position_in_detail(detail, recording_id)
        if pos is None:
            return None
        disc, position = pos
        mb_release = _build_mb_release(detail, [release_id])
        return mb_release, disc, position

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
