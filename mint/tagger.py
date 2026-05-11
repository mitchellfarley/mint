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
