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
    album: str = ""
    playlist_id: str = ""
    playlist_title: str = ""
    playlist_uploader: str = ""


def _clean_uploader(s: str) -> str:
    s = s.strip()
    for suffix in (" - Topic", "VEVO", "Vevo"):
        if s.endswith(suffix):
            s = s[: -len(suffix)].strip()
    return s


def _na(value: str) -> str:
    return "" if value == "NA" else value


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
    fmt = (
        "%(id)s\t%(title)s\t%(uploader)s\t"
        "%(artist,creator)s\t%(track)s\t%(album)s\t"
        "%(playlist_id)s\t%(playlist_title)s\t"
        "%(playlist_uploader,playlist_channel)s"
    )
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

    meta: dict[str, tuple[str, str, str, str, str, str, str, str]] = {}
    if meta_file.exists():
        for line in meta_file.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            parts = (parts + [""] * 9)[:9]
            vid, title, uploader, artist, track, album, pl_id, pl_title, pl_uploader = parts
            meta[vid] = (title, uploader, artist, track, album, pl_id, pl_title, pl_uploader)
        meta_file.unlink(missing_ok=True)

    result: list[DownloadedTrack] = []
    for mp3 in sorted(output_dir.glob("*.mp3")):
        title, uploader, artist, track, album, pl_id, pl_title, pl_uploader = meta.get(
            mp3.stem, (mp3.stem, "", "", "", "", "", "", "")
        )
        result.append(DownloadedTrack(
            path=mp3,
            title=title,
            uploader=_clean_uploader(uploader),
            artist=_na(artist),
            track=_na(track),
            album=_na(album),
            playlist_id=_na(pl_id),
            playlist_title=_na(pl_title),
            playlist_uploader=_clean_uploader(_na(pl_uploader)),
        ))
    return result
