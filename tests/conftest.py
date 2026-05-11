from pathlib import Path

import pytest
from mutagen.id3 import (
    ID3, ID3NoHeaderError,
    TIT2, TPE1, TPE2, TALB, TDRC, TRCK, TPOS, TCON, APIC,
)


# Minimal MPEG1 Layer3 frame: 128kbps, 44.1kHz, stereo, no CRC.
# Frame size = 144 * 128000 / 44100 = 417 bytes (no padding).
_MPEG_HEADER = bytes([0xff, 0xfb, 0x90, 0x00])
_SILENT_FRAME = _MPEG_HEADER + bytes(413)


@pytest.fixture
def make_mp3(tmp_path):
    counter = {"n": 0}

    def _make(
        name: str | None = None,
        tit2: str | None = None,
        tpe1: str | None = None,
        tpe2: str | None = None,
        talb: str | None = None,
        tdrc: str | None = None,
        trck: str | None = None,
        tpos: str | None = None,
        tcon: str | None = None,
        apic: bytes | None = None,
    ) -> Path:
        counter["n"] += 1
        fname = name or f"track_{counter['n']:03d}.mp3"
        path = tmp_path / fname
        path.write_bytes(_SILENT_FRAME)
        try:
            tags = ID3(str(path))
        except ID3NoHeaderError:
            tags = ID3()
        if tit2 is not None:
            tags.add(TIT2(encoding=3, text=tit2))
        if tpe1 is not None:
            tags.add(TPE1(encoding=3, text=tpe1))
        if tpe2 is not None:
            tags.add(TPE2(encoding=3, text=tpe2))
        if talb is not None:
            tags.add(TALB(encoding=3, text=talb))
        if tdrc is not None:
            tags.add(TDRC(encoding=3, text=tdrc))
        if trck is not None:
            tags.add(TRCK(encoding=3, text=trck))
        if tpos is not None:
            tags.add(TPOS(encoding=3, text=tpos))
        if tcon is not None:
            tags.add(TCON(encoding=3, text=tcon))
        if apic is not None:
            tags.add(APIC(encoding=0, mime="image/jpeg", type=3, desc="", data=apic))
        tags.save(str(path), v2_version=3)
        return path

    return _make
