from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


MARKER_BEGIN = "# >>> mint shell-init >>>"
MARKER_END = "# <<< mint shell-init <<<"

ZSH_SNIPPET = f"""{MARKER_BEGIN}
# Lets `mint add https://...?v=...` work without quoting the URL.
mint() {{ noglob command mint "$@"; }}
{MARKER_END}
"""

BASH_SNIPPET = f"""{MARKER_BEGIN}
# Bash does not glob `?` outside of pathname expansion contexts,
# so URLs are already safe. This block is a no-op placeholder.
{MARKER_END}
"""


@dataclass
class ShellInitResult:
    rc_file: Path
    installed: bool
    already_present: bool
    snippet: str


def _detect_rc() -> tuple[Path, str]:
    shell = os.environ.get("SHELL", "")
    home = Path.home()
    if shell.endswith("zsh"):
        return home / ".zshrc", ZSH_SNIPPET
    if shell.endswith("bash"):
        return home / ".bashrc", BASH_SNIPPET
    return home / ".zshrc", ZSH_SNIPPET


def run_shell_init(install: bool = False) -> ShellInitResult:
    rc_file, snippet = _detect_rc()

    if not install:
        print(snippet, end="")
        print()
        print(f"To install, run: mint shell-init --install")
        print(f"Or append manually to {rc_file}")
        return ShellInitResult(rc_file=rc_file, installed=False,
                                already_present=False, snippet=snippet)

    existing = rc_file.read_text() if rc_file.exists() else ""
    if MARKER_BEGIN in existing:
        print(f"Already installed in {rc_file}")
        return ShellInitResult(rc_file=rc_file, installed=False,
                                already_present=True, snippet=snippet)

    with rc_file.open("a") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n")
        f.write(snippet)

    print(f"Installed to {rc_file}")
    print("Restart your shell, or run: source " + str(rc_file))
    return ShellInitResult(rc_file=rc_file, installed=True,
                            already_present=False, snippet=snippet)
