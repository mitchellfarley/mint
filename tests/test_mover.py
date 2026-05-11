from mint.mover import destination_path, move_to_library


def test_destination_path_uses_track_number_padding(tmp_path):
    dest = destination_path(
        library_root=tmp_path,
        album_artist="Gorillaz",
        album="Demon Days",
        position=6,
        title="Feel Good Inc.",
    )
    assert dest == tmp_path / "Gorillaz" / "Demon Days" / "06 Feel Good Inc..mp3"


def test_destination_path_sanitizes_slashes(tmp_path):
    dest = destination_path(
        library_root=tmp_path,
        album_artist="AC/DC",
        album="Back/Slash",
        position=1,
        title="Hello/World",
    )
    assert dest == tmp_path / "AC_DC" / "Back_Slash" / "01 Hello_World.mp3"


def test_move_to_library_creates_dirs_and_moves(tmp_path):
    src = tmp_path / "src.mp3"
    src.write_bytes(b"audio")
    dst = tmp_path / "Library" / "Artist" / "Album" / "01 Song.mp3"
    move_to_library(src, dst)
    assert not src.exists()
    assert dst.exists()
    assert dst.read_bytes() == b"audio"
