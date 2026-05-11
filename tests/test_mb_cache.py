import time

from mint.mb_cache import MBCache


def test_cache_set_and_get(tmp_path):
    db = tmp_path / "mb.db"
    cache = MBCache(db)
    cache.set("artist::album", {"release_id": "abc", "title": "Alb"})
    assert cache.get("artist::album") == {"release_id": "abc", "title": "Alb"}


def test_cache_miss_returns_none(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    assert cache.get("missing") is None


def test_cache_overwrites_existing_key(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    cache.set("k", {"a": 1})
    cache.set("k", {"a": 2})
    assert cache.get("k") == {"a": 2}


def test_cover_blob_set_get(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    cache.set_cover("rid", b"\xff\xd8jpeg")
    assert cache.get_cover("rid") == b"\xff\xd8jpeg"


def test_cover_miss_returns_none(tmp_path):
    cache = MBCache(tmp_path / "mb.db")
    assert cache.get_cover("missing") is None
