from __future__ import annotations

import sys


def truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def format_eta(seconds: float) -> str:
    if seconds < 1:
        return "<1s"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60:02d}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60:02d}m"


def progress(idx: int, total: int, label: str, status: str,
             eta: str = "", label_width: int = 50) -> None:
    width = len(str(total))
    suffix = f"  ETA {eta}" if eta else ""
    line = f"[{idx:>{width}}/{total}] {truncate(label, label_width):<{label_width}} {status}{suffix}"
    sys.stdout.write("\r\x1b[2K" + line)
    sys.stdout.flush()


def progress_done(idx: int, total: int, label: str, status: str,
                   label_width: int = 50) -> None:
    progress(idx, total, label, status, label_width=label_width)
    sys.stdout.write("\n")
    sys.stdout.flush()
