from __future__ import annotations

import shutil
from pathlib import Path


def _sanitize(name: str) -> str:
    return name.replace("/", "_").replace(":", "_")


def destination_path(
    library_root: Path,
    album_artist: str,
    album: str,
    position: int,
    title: str,
) -> Path:
    return (
        library_root
        / _sanitize(album_artist)
        / _sanitize(album)
        / f"{position:02d} {_sanitize(title)}.mp3"
    )


def move_to_library(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
