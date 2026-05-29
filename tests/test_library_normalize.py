from mint.library import (
    normalize_artist_for_mb,
    normalize_for_mb_search,
    normalize_title_for_mb,
    primary_artist,
    strip_diacritics,
)


def test_strip_diacritics_basic():
    assert strip_diacritics("JAŸ-Z") == "JAY-Z"
    assert strip_diacritics("Beyoncé") == "Beyonce"
    assert strip_diacritics("RÜFÜS DU SOL") == "RUFUS DU SOL"


def test_strip_diacritics_no_change():
    assert strip_diacritics("Jay-Z") == "Jay-Z"


def test_primary_artist_takes_first_of_comma():
    assert primary_artist("JAŸ-Z, Kid Cudi") == "JAŸ-Z"


def test_primary_artist_takes_first_of_ampersand():
    assert primary_artist("Macklemore & Ryan Lewis") == "Macklemore"


def test_primary_artist_strips_feat_suffix():
    assert primary_artist("Drake feat. Some Guy") == "Drake"


def test_primary_artist_strips_feat_parens():
    assert primary_artist("Drake (feat. Some Guy)") == "Drake"


def test_primary_artist_x_separator():
    assert primary_artist("Diplo x Skrillex") == "Diplo"


def test_primary_artist_passthrough_single():
    assert primary_artist("Radiohead") == "Radiohead"


def test_normalize_artist_for_mb_combines():
    assert normalize_artist_for_mb("JAŸ-Z, Kid Cudi") == "JAY-Z"
    assert normalize_artist_for_mb("Beyoncé feat. Jay-Z") == "Beyonce"


def test_normalize_title_for_mb_strips_feat():
    assert normalize_title_for_mb("Already Home (feat. Kid Cudi)") == "Already Home"
    assert normalize_title_for_mb("Crazy In Love feat. Jay-Z") == "Crazy In Love"


def test_normalize_for_mb_search_collapses_whitespace():
    assert normalize_for_mb_search("  multiple   spaces  ") == "multiple spaces"
