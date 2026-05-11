from __future__ import annotations

import subprocess


def _osascript(script: str) -> int:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    return result.returncode


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def import_file(path: str) -> int:
    script = f'tell application "Music" to add POSIX file "{_escape(path)}"'
    return _osascript(script)


def remove_album(album: str) -> int:
    script = (
        f'tell application "Music"\n'
        f'  set found to (every track of library playlist 1 whose album is "{_escape(album)}")\n'
        f'  repeat with t in found\n'
        f'    delete t\n'
        f'  end repeat\n'
        f'end tell'
    )
    return _osascript(script)
