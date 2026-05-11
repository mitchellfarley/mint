from __future__ import annotations

import subprocess
from pathlib import Path


def download_url(spotify_url: str, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "spotdl",
            spotify_url,
            "--output", str(output_dir / "{title}.{output-ext}"),
            "--format", "mp3",
        ],
        cwd=str(output_dir),
        check=False,
    )
    return sorted(output_dir.rglob("*.mp3"))
