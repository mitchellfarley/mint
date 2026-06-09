```
           _       _    ⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣤⣄⣀⣀⡀⠀⠀⠀
 _ __ ___ (_)_ __ | |_  ⠀⠀⠀⠀⠀⢀⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⠶
| '_ ` _ \| | '_ \| __| ⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀
| | | | | | | | | | |_  ⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠀
|_| |_| |_|_|_| |_|\__| ⢀⣠⠞⠋⠉⠛⠻⠿⣿⣿⣿⠿⠟⠋⠀⠀⠀⠀⠀
                        ⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
```

# mint

YouTube → Apple Music with MusicBrainz-correct ID3 tags.

`mint` downloads music from YouTube, looks up the canonical metadata
(artist, album, track number, year) on MusicBrainz, writes correct ID3
tags and cover art, and imports the file into Apple Music.

## Install

Recommended (macOS, Homebrew Python): use [pipx](https://pipx.pypa.io/) so
`mint` lives in its own venv and is exposed on `PATH`.

```bash
brew install pipx
pipx ensurepath
pipx install git+https://github.com/mitchellfarley/mint.git
```

Restart your shell, then `mint` is available globally. Upgrade later with
either:

```bash
mint update          # uses pipx if available, otherwise pip
pipx upgrade mint    # equivalent direct invocation
```

Alternatively, install into a virtual environment with pip:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/mitchellfarley/mint.git
```

Or from a local clone, for development:

```bash
git clone https://github.com/mitchellfarley/mint.git
cd mint
pip install -e .
```

## Requirements

- macOS (uses `osascript` to import into Apple Music)
- Python 3.12+
- [ffmpeg](https://ffmpeg.org/) on `PATH` (required by yt-dlp for mp3 extraction)
- Apple Music app installed

## Commands

Run `mint` with no arguments to see the help screen:

```
Usage:
  mint <command> [args]

Commands:
  add <url>   download YouTube URL, tag, import into Apple Music
  clean       audit library, propose ID3 fixes, apply on approval
  dup         find and remove duplicate tracks, albums, artists
  update      upgrade mint to the latest version from GitHub
  version     print the installed version
  help        show this help
```

`mint --version` and `mint -v` are equivalent to `mint version`.

### `mint add <url>`

Download a YouTube video or playlist, tag from MusicBrainz, import.

```bash
mint add "https://www.youtube.com/watch?v=VIDEO_ID"
mint add "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

Pipeline per track:

1. yt-dlp downloads audio as mp3 into `~/Music/staging/`
2. Artist and track are resolved from yt-dlp metadata, then the
   video title, then the uploader name (see fallback chain below)
3. MusicBrainz recording search resolves the canonical release,
   disc, and position
4. ID3 tags written: title, artist, album artist, album, year,
   track number, disc number, genre, cover art
5. File moved to
   `~/Music/Music/Media.localized/Music/<Artist>/<Album>/NN Title.mp3`
6. Apple Music imports the file via AppleScript

Output:

```
[1/3] imported   Karma Police                              done
[2/3] duplicate  Creep                                     skipped
[3/3] failed     RANDOM_TITLE                              unparseable title

Summary
  imported    1
  skipped     1  (duplicate)
  failed      1
  Failed tracks:
    - RANDOM_TITLE
```

**How artist and track are resolved.** Per download, mint tries
three sources in order:

1. yt-dlp's `artist` and `track` metadata fields, if both are
   present. This covers most YouTube Music and Topic-channel
   uploads, where the canonical artist/track are attached as
   metadata regardless of the visible video title.
2. Title parsing: `Artist - Track`, `Artist | Track`, or
   `Artist — Track`, with noise like `(Official Video)`,
   `[Lyrics]`, `4K` stripped.
3. Uploader name as artist plus the full video title as track.
   This is a guess and can still produce wrong MusicBrainz
   matches (e.g. an unrelated cover, or no match at all), so
   results from this fallback should be sanity-checked.

Only if all three fail (no artist or no title resolved) is the
download reported as `unparseable title` and left in the staging
directory.

### `mint clean`

Audit the existing library, report tag issues, apply fixes after
approval. Checks for:

- Missing or wrong disc/track numbers
- `feat.` artists incorrectly placed in TPE1
- TPE1 ≠ TPE2 (artist vs. album artist mismatch)
- Wrong year, title, album, or track number
- Genre inconsistent across an artist's library
- Missing cover art
- MusicBrainz lookup failures

### `mint dup`

Scan the library for duplicate artists, albums, and tracks.

Detection is normalized: a leading `The ` is dropped from artist
names, and artist/album/track strings are compared via the same
normalization used by `mint add` (case, punctuation, and
whitespace folded). Artists are keyed off TPE2 (album artist)
when present, else TPE1.

Three reports are produced:

- **Duplicate artists.** Same normalized artist appearing under
  multiple spellings (e.g. `Beyoncé` vs `Beyonce`). Reported
  only; manual rename/merge is required.
- **Duplicate albums.** Same `(artist, album)` key with files
  living under more than one directory. Reported only; manual
  merge is required.
- **Duplicate tracks.** Same `(artist, title)` key across
  multiple files. The first file in each group is kept; the
  rest are flagged for deletion. After confirmation (`y`), the
  extra files are unlinked from disk and removed from Apple
  Music via AppleScript.

No deletions occur without an explicit `y` prompt.

## Configuration

Edit `mint/config.py`:

- `LIBRARY_ROOT` — Apple Music library path
  (default: `~/Music/Music/Media.localized/Music`)
- `STAGING_DIR` — where yt-dlp writes mp3s before tagging
  (default: `~/Music/staging`)
- `CACHE_DB` — sqlite cache of MusicBrainz responses and cover art
  (default: `~/.cache/mint/mb_cache.db`)
- `MB_USER_AGENT` — MusicBrainz API user agent (name, version, contact)

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
