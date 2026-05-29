from __future__ import annotations

import argparse
import sys

from mint.banner import render_banner
from mint.commands.add import run_add
from mint.commands.clean import run_clean
from mint.commands.update import run_update
from mint.config import CACHE_DB, LIBRARY_ROOT, MB_USER_AGENT, STAGING_DIR


COMMANDS = [
    ("add <url>", "download YouTube URL, tag, import into Apple Music"),
    ("clean",     "audit library, propose ID3 fixes, apply on approval"),
    ("update",    "upgrade mint to the latest version from GitHub"),
    ("help",      "show this help"),
]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mint", add_help=False)
    sub = p.add_subparsers(dest="command")
    add_p = sub.add_parser("add", add_help=False)
    add_p.add_argument("url")
    sub.add_parser("clean", add_help=False)
    sub.add_parser("update", add_help=False)
    sub.add_parser("help", add_help=False)
    return p


def render_help() -> str:
    width = max(len(name) for name, _ in COMMANDS)
    lines = ["Usage:", "  mint <command> [args]", "", "Commands:"]
    for name, desc in COMMANDS:
        lines.append(f"  {name:<{width}}   {desc}")
    lines.append("")
    lines.append("Examples:")
    lines.append("  mint add https://www.youtube.com/watch?v=VIDEO_ID")
    lines.append("  mint clean")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    print(render_banner())
    print()
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        print(render_help())
        return 2

    if args.command == "add":
        summary = run_add(
            youtube_url=args.url,
            library_root=LIBRARY_ROOT,
            staging_dir=STAGING_DIR,
            cache_db=CACHE_DB,
            user_agent=MB_USER_AGENT,
        )
        print()
        print("Summary")
        print(f"  imported  {summary.imported:>3}")
        print(f"  skipped   {summary.skipped:>3}  (duplicate)")
        print(f"  failed    {summary.failed:>3}")
        if summary.failed_titles:
            print("  Failed tracks:")
            for t in summary.failed_titles:
                print(f"    - {t}")
        return 0

    if args.command == "clean":
        run_clean(
            library_root=LIBRARY_ROOT,
            cache_db=CACHE_DB,
            user_agent=MB_USER_AGENT,
        )
        return 0

    if args.command == "update":
        result = run_update()
        return result.returncode

    print(render_help())
    return 0 if args.command == "help" else 2


if __name__ == "__main__":
    sys.exit(main())
