from unittest.mock import MagicMock, patch

import pytest

from mint.mb_cache import MBCache
from mint.mb_client import MBClient, cache_key


def test_cache_key_normalizes():
    assert cache_key("The Weeknd", "Timeless") == cache_key("the weeknd", "timeless")
    assert cache_key("RÜFÜS DU SOL", "Bloom") == cache_key("rüfüs du sol", "bloom")


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


def test_lookup_recording_returns_release_and_position(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_recordings.return_value = _fake_recording_search()
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
    with patch("mint.mb_client.musicbrainzngs") as mb:
        mb.search_recordings.return_value = _fake_recording_search()
        mb.get_release_by_id.return_value = _fake_release_detail()
        client = MBClient(cache=cache)
        client.lookup_recording("Gorillaz", "Feel Good Inc.")
        client.lookup_recording("Gorillaz", "Feel Good Inc.")
    assert mb.search_recordings.call_count == 1
    assert mb.get_release_by_id.call_count == 1
