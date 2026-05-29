from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DownloadedTrack:
    path: Path
    title: str
    uploader: str
    artist: str
    track: str


def _clean_uploader(s: str) -> str:
    s = s.strip()
    for suffix in (" - Topic", "VEVO", "Vevo"):
        if s.endswith(suffix):
            s = s[: -len(suffix)].strip()
    return s


def download_url(
    youtube_url: str,
    output_dir: Path,
    quiet: bool = True,
) -> list[DownloadedTrack]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(id)s.%(ext)s")
    meta_file = output_dir / ".titles.tsv"
    if meta_file.exists():
        meta_file.unlink()
    fmt = "%(id)s\t%(title)s\t%(uploader)s\t%(artist,creator,uploader)s\t%(track,title)s"
    cmd = [
        sys.executable, "-m", "yt_dlp",
        youtube_url,
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", output_template,
        "--print-to-file", fmt, str(meta_file),
        "--no-progress",
    ]
    if quiet:
        cmd.extend(["--quiet", "--no-warnings"])
    subprocess.run(cmd, cwd=str(output_dir), check=False)

    meta: dict[str, tuple[str, str, str, str]] = {}
    if meta_file.exists():
        for line in meta_file.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            vid, title, uploader, artist, track = parts[:5]
            meta[vid] = (title, uploader, artist, track)
        meta_file.unlink(missing_ok=True)

    result: list[DownloadedTrack] = []
    for mp3 in sorted(output_dir.rglob("*.mp3")):
        title, uploader, artist, track = meta.get(
            mp3.stem, (mp3.stem, "", "", "")
        )
        result.append(DownloadedTrack(
            path=mp3,
            title=title,
            uploader=_clean_uploader(uploader),
            artist=artist if artist != "NA" else "",
            track=track if track != "NA" else "",
        ))
    return result
