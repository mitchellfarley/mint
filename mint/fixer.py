from __future__ import annotations

from pathlib import Path

from mint.auditor import ProposedTags
from mint.tagger import write_cover, write_tags


def apply_proposed(
    path: Path,
    proposed: ProposedTags,
    cover_data: bytes | None,
) -> None:
    write_tags(
        path,
        tit2=proposed.tit2,
        tpe1=proposed.tpe1,
        tpe2=proposed.tpe2,
        talb=proposed.talb,
        tdrc=proposed.tdrc,
        trck=proposed.trck,
        tpos=proposed.tpos,
        tcon=proposed.tcon,
    )
    if cover_data is not None:
        write_cover(path, cover_data)
