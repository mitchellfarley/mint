from __future__ import annotations

from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError

from mint.models import Track


def _frame_text(tags: ID3 | None, key: str) -> str:
    if tags is None:
        return ""
    frame = tags.get(key)
    if frame is None:
        return ""
    return str(frame)


def read_track(path: Path) -> Track:
    try:
        tags = ID3(str(path))
    except ID3NoHeaderError:
        tags = None
    has_apic = False
    if tags is not None:
        has_apic = any(k.startswith("APIC") for k in tags.keys())
    return Track(
        path=path,
        tit2=_frame_text(tags, "TIT2"),
        tpe1=_frame_text(tags, "TPE1"),
        tpe2=_frame_text(tags, "TPE2"),
        talb=_frame_text(tags, "TALB"),
        tdrc=_frame_text(tags, "TDRC"),
        trck=_frame_text(tags, "TRCK"),
        tpos=_frame_text(tags, "TPOS"),
        tcon=_frame_text(tags, "TCON"),
        has_apic=has_apic,
    )


from mutagen.id3 import (
    TIT2, TPE1, TPE2, TALB, TDRC, TRCK, TPOS, TCON, APIC,
)


_FRAME_FACTORIES = {
    "tit2": ("TIT2", TIT2),
    "tpe1": ("TPE1", TPE1),
    "tpe2": ("TPE2", TPE2),
    "talb": ("TALB", TALB),
    "tdrc": ("TDRC", TDRC),
    "trck": ("TRCK", TRCK),
    "tpos": ("TPOS", TPOS),
    "tcon": ("TCON", TCON),
}


def _open_tags(path: Path) -> ID3:
    try:
        return ID3(str(path))
    except ID3NoHeaderError:
        return ID3()


def write_tags(
    path: Path,
    *,
    tit2: str | None = None,
    tpe1: str | None = None,
    tpe2: str | None = None,
    talb: str | None = None,
    tdrc: str | None = None,
    trck: str | None = None,
    tpos: str | None = None,
    tcon: str | None = None,
) -> None:
    tags = _open_tags(path)
    values = {
        "tit2": tit2, "tpe1": tpe1, "tpe2": tpe2, "talb": talb,
        "tdrc": tdrc, "trck": trck, "tpos": tpos, "tcon": tcon,
    }
    for key, value in values.items():
        if value is None:
            continue
        frame_id, factory = _FRAME_FACTORIES[key]
        tags.delall(frame_id)
        tags.add(factory(encoding=3, text=value))
    tags.save(str(path), v2_version=3)


def write_cover(path: Path, jpeg_data: bytes) -> None:
    tags = _open_tags(path)
    tags.delall("APIC")
    tags.add(APIC(encoding=0, mime="image/jpeg", type=3, desc="", data=jpeg_data))
    tags.save(str(path), v2_version=3)
