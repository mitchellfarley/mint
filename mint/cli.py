from __future__ import annotations

import argparse
import sys

from mint.banner import render_banner
from mint.commands.add import run_add
from mint.commands.fix import run_fix
from mint.config import CACHE_DB, LIBRARY_ROOT, MB_USER_AGENT, STAGING_DIR


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mint", description="Spotify → Apple Music")
    sub = p.add_subparsers(dest="command")
    add_p = sub.add_parser("add", help="download Spotify URL and import")
    add_p.add_argument("url", help="Spotify track/album/playlist URL")
    sub.add_parser("fix", help="audit library and apply fixes")
    return p


def main(argv: list[str] | None = None) -> int:
    print(render_banner())
    print()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "add":
        summary = run_add(
            spotify_url=args.url,
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

    if args.command == "fix":
        run_fix(
            library_root=LIBRARY_ROOT,
            cache_db=CACHE_DB,
            user_agent=MB_USER_AGENT,
        )
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
