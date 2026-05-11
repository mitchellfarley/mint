from pathlib import Path

from mint.config import LIBRARY_ROOT, STAGING_DIR, CACHE_DB, MB_USER_AGENT


def test_paths_under_home():
    home = Path.home()
    assert LIBRARY_ROOT == home / "Music/Music/Media.localized/Music"
    assert STAGING_DIR == home / "Music/staging"
    assert CACHE_DB == home / ".cache/mint/mb_cache.db"


def test_user_agent_set():
    assert MB_USER_AGENT[0] == "mint"
    assert MB_USER_AGENT[1] == "0.1.0"
    assert "@" in MB_USER_AGENT[2]
