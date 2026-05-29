from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def download_url(youtube_url: str, output_dir: Path) -> list[tuple[Path, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(id)s.%(ext)s")
    proc = subprocess.run(
        [
            sys.executable, "-m", "yt_dlp",
            youtube_url,
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", output_template,
            "--print-to-file", "%(id)s\t%(title)s", str(output_dir / ".titles.tsv"),
            "--no-progress",
        ],
        cwd=str(output_dir),
        check=False,
    )
    titles_file = output_dir / ".titles.tsv"
    titles: dict[str, str] = {}
    if titles_file.exists():
        for line in titles_file.read_text().splitlines():
            if "\t" not in line:
                continue
            vid, title = line.split("\t", 1)
            titles[vid] = title
        titles_file.unlink(missing_ok=True)

    result: list[tuple[Path, str]] = []
    for mp3 in sorted(output_dir.rglob("*.mp3")):
        title = titles.get(mp3.stem, mp3.stem)
        result.append((mp3, title))
    return result
