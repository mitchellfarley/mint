from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_URL = "git+https://github.com/mitchellfarley/mint.git"


@dataclass
class UpdateResult:
    method: str
    returncode: int


def _detect_method() -> str:
    exe = Path(sys.executable).resolve()
    if "pipx" in exe.parts:
        return "pipx"
    if shutil.which("pipx"):
        return "pipx"
    return "pip"


def run_update() -> UpdateResult:
    method = _detect_method()
    if method == "pipx":
        cmd = ["pipx", "upgrade", "mint"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", REPO_URL]

    print(f"Updating via: {' '.join(cmd)}")
    print()
    proc = subprocess.run(cmd)
    return UpdateResult(method=method, returncode=proc.returncode)
