#!/usr/bin/env python3
"""
YouTube Live -> M3U converter.

Reads sources.txt (one channel/live link per line, optional "Name | URL" format),
resolves each to a live .m3u8 stream URL using yt-dlp, and writes playlist.m3u.

Run manually:
    python extract_stream.py

Designed to run on a schedule via GitHub Actions (see .github/workflows/update_playlist.yml).
"""

import sys
import re
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Run: pip install yt-dlp", file=sys.stderr)
    sys.exit(1)

SOURCES_FILE = Path("sources.txt")
OUTPUT_FILE = Path("playlist.m3u")

YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "format": "best[ext=mp4]/best",
    "extract_flat": False,
    "noplaylist": True,
}


def parse_sources(path: Path):
    """Parse sources.txt into a list of (name_or_none, url) tuples."""
    entries = []
    if not path.exists():
        print(f"Source file not found: {path}", file=sys.stderr)
        return entries

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "|" in line:
            name, url = line.split("|", 1)
            name = name.strip()
            url = url.strip()
        else:
            name = None
            url = line.strip()

        if url:
            entries.append((name or None, url))

    return entries


def resolve_stream(url: str):
    """
    Use yt-dlp to resolve a channel/live/video URL into:
      - title (str)
      - stream_url (str, the actual .m3u8 / direct media URL)
    Returns (None, None) on failure (e.g. channel not currently live).
    """
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        print(f"  -> FAILED: {url}  ({exc})", file=sys.stderr)
        return None, None

    if info is None:
        return None, None

    # extract_info on a channel "/live" URL can return a playlist-style dict
    # with 'entries'; grab the first live entry if so.
    if "entries" in info and info["entries"]:
        info = next((e for e in info["entries"] if e), None)
        if info is None:
            return None, None

    is_live = info.get("is_live") or info.get("live_status") == "is_live"
    if not is_live:
        print(f"  -> NOT LIVE right now: {url}", file=sys.stderr)
        return None, None

    title = info.get("title", "Untitled Stream")
    stream_url = info.get("url")

    # Fallback: pick best m3u8 format from formats list if top-level url missing
    if not stream_url:
        formats = info.get("formats") or []
        m3u8_formats = [f for f in formats if f.get("protocol", "").startswith("m3u8")]
        if m3u8_formats:
            stream_url = m3u8_formats[-1]["url"]

    if not stream_url:
        print(f"  -> No playable stream URL found: {url}", file=sys.stderr)
        return None, None

    return title, stream_url


def sanitize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


def build_playlist(entries):
    lines = ["#EXTM3U"]
    success_count = 0

    for custom_name, url in entries:
        print(f"Checking: {custom_name or url}")
        title, stream_url = resolve_stream(url)

        if not stream_url:
            continue

        display_name = sanitize_name(custom_name or title)
        lines.append(f'#EXTINF:-1 tvg-name="{display_name}",{display_name}')
        lines.append(stream_url)
        success_count += 1
        print(f"  -> OK: {display_name}")

    return lines, success_count


def main():
    entries = parse_sources(SOURCES_FILE)
    if not entries:
        print("No sources found in sources.txt. Nothing to do.", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(entries)} source link(s). Resolving live streams...\n")
    lines, success_count = build_playlist(entries)

    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nDone. {success_count}/{len(entries)} channel(s) live and added to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
