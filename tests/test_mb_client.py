from unittest.mock import MagicMock, patch

import pytest

from mint.mb_cache import MBCache
from mint.mb_client import MBClient, cache_key


def test_cache_key_normalizes():
    assert cache_key("The Weeknd", "Timeless") == cache_key("the weeknd", "timeless")
    assert cache_key("RÜFÜS DU SOL", "Bloom") == cache_key("rüfüs du sol", "bloom")


def test_cache_key_strips_diacritics():
    assert cache_key("Beyoncé", "Lemonade") == cache_key("Beyonce", "Lemonade")
    assert cache_key("Sigur Rós", "Takk") == cache_key("Sigur Ros", "Takk")
    assert cache_key("Café", "naïve") == cache_key("Cafe", "naive")


def test_cache_key_collapses_whitespace():
    assert cache_key("  The  Band  ", "Album") == cache_key("The Band", "Album")
    assert cache_key("a\tb", "c") == cache_key("a b", "c")


def _fake_search_result():
    return {
        "release-list": [
            {
                "id": "rid-1",
                "title": "Demon Days",
                "date": "2005-05-11",
                "country": "US",
                "status": "Official",
                "artist-credit-phrase": "Gorillaz",
            }
        ]
    }


def _fake_release_detail():
    return {
        "release": {
            "id": "rid-1",
            "title": "Demon Days",
            "date": "2005-05-11",
            "artist-credit-phrase": "Gorillaz",
            "medium-list": [
                {
                    "position": "1",
                    "track-count": 2,
                    "track-list": [
                        {"position": "1", "recording": {"id": "rec1", "title": "Intro"}},
                        {"position": "2", "recording": {"id": "rec2", "title": "Feel Good Inc."}},
                    ],
                }
            ],
        }
    }


def test_lookup_release_caches_and_returns(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_releases.return_value = _fake_search_result()
        mb.get_release_by_id.return_value = _fake_release_detail()
        client = MBClient(cache=cache)
        rel = client.lookup_release("Gorillaz", "Demon Days")
    assert rel is not None
    assert rel.release_id == "rid-1"
    assert rel.artist_credit_phrase == "Gorillaz"
    assert rel.year == "2005"
    assert rel.tracks[(1, 2)].title == "Feel Good Inc."
    assert rel.tracks[(1, 2)].total_tracks == 2


def test_lookup_release_uses_cache_on_second_call(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_releases.return_value = _fake_search_result()
        mb.get_release_by_id.return_value = _fake_release_detail()
        client = MBClient(cache=cache)
        client.lookup_release("Gorillaz", "Demon Days")
        client.lookup_release("Gorillaz", "Demon Days")
    assert mb.search_releases.call_count == 1
    assert mb.get_release_by_id.call_count == 1


def test_lookup_release_no_match_returns_none(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_releases.return_value = {"release-list": []}
        client = MBClient(cache=cache)
        rel = client.lookup_release("Unknown", "Unknown")
    assert rel is None


def test_fetch_cover_tries_multiple_release_ids(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    with patch("mint.mb_client.requests.get") as get:
        r1 = MagicMock(status_code=404)
        r2 = MagicMock(status_code=200, content=b"jpegdata")
        get.side_effect = [r1, r2]
        client = MBClient(cache=cache)
        data = client.fetch_cover(["rid-1", "rid-2"])
    assert data == b"jpegdata"


def test_fetch_cover_caches(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    with patch("mint.mb_client.requests.get") as get:
        get.return_value = MagicMock(status_code=200, content=b"jpegdata")
        client = MBClient(cache=cache)
        client.fetch_cover(["rid-1"])
        client.fetch_cover(["rid-1"])
    assert get.call_count == 1


def _fake_recording_search():
    return {
        "recording-list": [
            {
                "id": "rec2",
                "title": "Feel Good Inc.",
                "release-list": [
                    {
                        "id": "rid-1",
                        "title": "Demon Days",
                        "date": "2005-05-11",
                        "country": "US",
                        "status": "Official",
                        "release-group": {"primary-type": "Album"},
                        "medium-list": [
                            {
                                "position": "1",
                                "track-count": 2,
                                "track-list": [
                                    {"position": "1", "id": "t1", "recording": {"id": "rec1"}},
                                    {"position": "2", "id": "t2", "recording": {"id": "rec2"}},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }


def _fake_browse_releases_for(rec_id_to_releases):
    def _impl(recording=None, includes=None, limit=None):
        return {"release-list": rec_id_to_releases.get(recording, [])}
    return _impl


def test_lookup_recording_returns_release_and_position(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    rec_releases = _fake_recording_search()["recording-list"][0]["release-list"]
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_recordings.return_value = _fake_recording_search()
        mb.browse_releases.side_effect = _fake_browse_releases_for(
            {"rec2": rec_releases}
        )
        mb.get_release_by_id.return_value = _fake_release_detail()
        client = MBClient(cache=cache)
        got = client.lookup_recording("Gorillaz", "Feel Good Inc.")
    assert got is not None
    rel, disc, position = got
    assert rel.release_id == "rid-1"
    assert disc == 1
    assert position == 2


def test_lookup_recording_no_match_returns_none(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_recordings.return_value = {"recording-list": []}
        client = MBClient(cache=cache)
        assert client.lookup_recording("Unknown", "Unknown") is None


def test_lookup_recording_uses_cache_on_second_call(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    rec_releases = _fake_recording_search()["recording-list"][0]["release-list"]
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_recordings.return_value = _fake_recording_search()
        mb.browse_releases.side_effect = _fake_browse_releases_for(
            {"rec2": rec_releases}
        )
        mb.get_release_by_id.return_value = _fake_release_detail()
        client = MBClient(cache=cache)
        client.lookup_recording("Gorillaz", "Feel Good Inc.")
        client.lookup_recording("Gorillaz", "Feel Good Inc.")
    assert mb.search_recordings.call_count == 1
    assert mb.get_release_by_id.call_count == 1


def test_lookup_release_prefers_album_over_single_same_year(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    search = {
        "release-list": [
            {
                "id": "single-1",
                "title": "Rich Flex",
                "date": "2022-10-21",
                "country": "US",
                "status": "Official",
                "artist-credit-phrase": "Drake & 21 Savage",
                "release-group": {"primary-type": "Single"},
            },
            {
                "id": "album-1",
                "title": "Her Loss",
                "date": "2022-11-04",
                "country": "US",
                "status": "Official",
                "artist-credit-phrase": "Drake & 21 Savage",
                "release-group": {"primary-type": "Album"},
            },
        ]
    }
    detail = {
        "release": {
            "id": "album-1",
            "title": "Her Loss",
            "date": "2022-11-04",
            "artist-credit-phrase": "Drake & 21 Savage",
            "medium-list": [
                {
                    "position": "1",
                    "track-count": 1,
                    "track-list": [
                        {"position": "1", "recording": {"id": "r1", "title": "Rich Flex"}},
                    ],
                }
            ],
        }
    }
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_releases.return_value = search
        mb.get_release_by_id.return_value = detail
        client = MBClient(cache=cache)
        rel = client.lookup_release("Drake & 21 Savage", "Her Loss")
    assert rel is not None
    assert rel.release_id == "album-1"
    args, kwargs = mb.get_release_by_id.call_args
    assert args[0] == "album-1"


def _fake_recording_search_ambiguous():
    return {
        "recording-list": [
            {
                "id": "rec-a",
                "title": "Rich Flex",
                "artist-credit-phrase": "Drake & 21 Savage",
                "release-list": [
                    {
                        "id": "album-1",
                        "title": "Her Loss",
                        "date": "2022-11-04",
                        "country": "US",
                        "status": "Official",
                        "release-group": {"primary-type": "Album"},
                    }
                ],
            },
            {
                "id": "rec-b",
                "title": "Rich Flex",
                "artist-credit-phrase": "Various Artists",
                "release-list": [
                    {
                        "id": "comp-1",
                        "title": "Now 113",
                        "date": "2022-11-18",
                        "country": "GB",
                        "status": "Official",
                        "release-group": {"primary-type": "Album"},
                    }
                ],
            },
            {
                "id": "rec-c",
                "title": "Rich Flex",
                "artist-credit-phrase": "Drake & 21 Savage",
                "release-list": [
                    {
                        "id": "album-2",
                        "title": "Her Loss (Deluxe)",
                        "date": "2023-01-01",
                        "country": "US",
                        "status": "Official",
                        "release-group": {"primary-type": "Album"},
                    }
                ],
            },
        ]
    }


def test_lookup_recording_calls_prompter_when_ambiguous(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    detail = {
        "release": {
            "id": "album-2",
            "title": "Her Loss (Deluxe)",
            "date": "2023-01-01",
            "artist-credit-phrase": "Drake & 21 Savage",
            "medium-list": [
                {
                    "position": "1",
                    "track-count": 1,
                    "track-list": [
                        {"position": "1", "recording": {"id": "rec-c", "title": "Rich Flex"}},
                    ],
                }
            ],
        }
    }
    seen: list[list[dict]] = []

    def prompter(cands):
        seen.append(cands)
        return 1

    ambig = _fake_recording_search_ambiguous()
    rec_releases_map = {
        r["id"]: r["release-list"]
        for r in ambig["recording-list"]
    }
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_recordings.return_value = ambig
        mb.browse_releases.side_effect = _fake_browse_releases_for(rec_releases_map)
        mb.get_release_by_id.return_value = detail
        client = MBClient(cache=cache)
        got = client.lookup_recording("Drake", "Rich Flex", prompter=prompter)
    assert got is not None
    rel, disc, position = got
    # Various Artists rec-b is filtered out by the artist match. Prompter
    # sees the remaining two Drake & 21 Savage candidates, picks idx 1.
    assert rel.release_id == "album-2"
    assert len(seen) == 1
    assert len(seen[0]) == 2
    assert all("Drake" in c["artist"] for c in seen[0])


def test_lookup_recording_prompter_skip_returns_none(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    ambig = _fake_recording_search_ambiguous()
    rec_releases_map = {
        r["id"]: r["release-list"]
        for r in ambig["recording-list"]
    }
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_recordings.return_value = ambig
        mb.browse_releases.side_effect = _fake_browse_releases_for(rec_releases_map)
        client = MBClient(cache=cache)
        got = client.lookup_recording(
            "Drake", "Rich Flex", prompter=lambda c: None,
        )
    assert got is None


def test_lookup_recording_no_prompt_when_single_candidate(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    calls: list[list[dict]] = []
    rec_releases = _fake_recording_search()["recording-list"][0]["release-list"]
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_recordings.return_value = _fake_recording_search()
        mb.browse_releases.side_effect = _fake_browse_releases_for(
            {"rec2": rec_releases}
        )
        mb.get_release_by_id.return_value = _fake_release_detail()
        client = MBClient(cache=cache)
        client.lookup_recording(
            "Gorillaz", "Feel Good Inc.",
            prompter=lambda c: (calls.append(c), 0)[1],
        )
    assert calls == []
