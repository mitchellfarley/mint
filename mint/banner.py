from __future__ import annotations

from pyfiglet import Figlet

from mint import __version__


_LEAF = (
    "⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣤⣄⣀⣀⡀⠀⠀⠀\n"
    "⠀⠀⠀⠀⠀⢀⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⠶\n"
    "⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀\n"
    "⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠀\n"
    "⢀⣠⠞⠋⠉⠛⠻⠿⣿⣿⣿⠿⠟⠋⠀⠀⠀⠀⠀\n"
    "⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
)


def render_banner() -> str:
    fig = Figlet(font="standard")
    art = fig.renderText("mint").rstrip("\n")
    tagline = f"mint v{__version__} — youtube → apple music"
    return f"{art}\n\n{_LEAF}\n\n{tagline}"
