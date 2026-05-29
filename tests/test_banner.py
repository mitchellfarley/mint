from mint.banner import render_banner


def test_banner_contains_word_mint():
    out = render_banner()
    assert "mint" in out.lower()


def test_banner_contains_version_and_tagline():
    from mint import __version__
    out = render_banner()
    assert f"v{__version__}" in out
    assert "youtube" in out.lower()
    assert "apple music" in out.lower()


def test_banner_is_multiline_ascii():
    out = render_banner()
    assert out.count("\n") >= 4
