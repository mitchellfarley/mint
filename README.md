```
                _         _
  _ __ ___ (_)_ __ | |_
 | '_ ` _ \| | '_ \| __|
 | | | | | | | | | | |_
 |_| |_| |_|_|_| |_|\__|
```

# mint

YouTube → Apple Music with MusicBrainz-correct ID3 tags.

`mint` downloads music from YouTube, looks up the canonical metadata
(artist, album, track number, year) on MusicBrainz, writes correct ID3
tags and cover art, and imports the file into Apple Music.

## Install

```bash
pip install git+https://github.com/mitchellfarley/mint.git
```

Or, from a local clone:

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
  fix         audit library, propose ID3 fixes, apply on approval
  help        show this help
```

### `mint add <url>`

Download a YouTube video or playlist, tag from MusicBrainz, import.

```bash
mint add "https://www.youtube.com/watch?v=VIDEO_ID"
mint add "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

Pipeline per track:

1. yt-dlp downloads audio as mp3 into `~/Music/staging/`
2. The video title is parsed as `Artist - Track` (noise like
   `(Official Video)`, `[Lyrics]`, `4K` is stripped)
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

**Title format requirement.** The parser expects `Artist - Track`
(or `Artist | Track`, `Artist — Track`). Videos with non-standard
titles (e.g. `ColdplayVEVO` channel uploading `Yellow` with no
separator) are reported as `unparseable title` and left in the
staging directory.

### `mint fix`

Audit the existing library, report tag issues, apply fixes after
approval. Checks for:

- Missing or wrong disc/track numbers
- `feat.` artists incorrectly placed in TPE1
- TPE1 ≠ TPE2 (artist vs. album artist mismatch)
- Wrong year, title, album, or track number
- Genre inconsistent across an artist's library
- Missing cover art
- MusicBrainz lookup failures

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
