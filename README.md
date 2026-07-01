# YouTube Live → M3U Converter

Auto-generates an M3U playlist from a list of YouTube channel/live links,
refreshed every 6 hours via GitHub Actions.

## Setup

1. Push this repo to GitHub.
2. Edit `sources.txt` — add one link per line, either:
   - `Name | https://www.youtube.com/@channel/live`
   - or just the bare URL (the channel's own title will be used)
3. Make sure repo settings allow GitHub Actions to push:
   Settings → Actions → General → Workflow permissions → **Read and write permissions**.
4. The workflow `.github/workflows/update_playlist.yml` runs:
   - every 6 hours (cron),
   - on manual trigger (Actions tab → Run workflow),
   - automatically whenever you edit `sources.txt`.
5. Output: `playlist.m3u` is committed back to the repo each run.
   Use the raw GitHub URL in any IPTV player:
   `https://raw.githubusercontent.com/<user>/<repo>/main/playlist.m3u`

## Local test

```bash
pip install -r requirements.txt
python extract_stream.py
```

## Notes

- Channels that aren't currently live are skipped that run (logged to stderr) — no broken entries in the playlist.
- `m3u8` URLs from YouTube expire after a few hours, which is exactly why the 6-hour re-scan keeps the playlist working.
- To go more/less frequent, edit the cron line in the workflow, e.g. `0 */3 * * *` for every 3 hours.
