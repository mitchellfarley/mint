from __future__ import annotations

from pyfiglet import Figlet

from mint import __version__


_LEAF_LINES = [
    "⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣤⣄⣀⣀⡀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⢀⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⠶",
    "⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀",
    "⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠀",
    "⢀⣠⠞⠋⠉⠛⠻⠿⣿⣿⣿⠿⠟⠋⠀⠀⠀⠀⠀",
    "⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
]


def render_banner() -> str:
    fig = Figlet(font="standard")
    art_lines = fig.renderText("mint").rstrip("\n").split("\n")
    art_width = max(len(line) for line in art_lines)

    rows = []
    n = max(len(art_lines), len(_LEAF_LINES))
    for i in range(n):
        left = art_lines[i] if i < len(art_lines) else ""
        right = _LEAF_LINES[i] if i < len(_LEAF_LINES) else ""
        rows.append(f"{left:<{art_width}} {right}")

    banner = "\n".join(rows)
    tagline = f"mint v{__version__} — youtube → apple music"
    return f"{banner}\n\n{tagline}"
