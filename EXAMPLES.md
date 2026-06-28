# YT Helper — Examples

Practical recipes for the three layers of `yt-helper`. Every snippet
assumes:

```python
import yt_helper as yth
```

and that `yt-dlp` + `ffmpeg` are installed (`brew install yt-dlp ffmpeg`
on macOS).

---

## Table of Contents

1. [Setup](#setup)
2. [Downloads (to disk)](#downloads-to-disk)
3. [Stream Catalog & Picker](#stream-catalog--picker)
4. [Direct-URL Resolver](#direct-url-resolver)
5. [Composing with video-helper](#composing-with-video-helper)
6. [Branding — engagement metadata without API keys](#branding--engagement-metadata-without-api-keys)
7. [Subtitles, Comments, Channels](#subtitles-comments-channels)
8. [Caveats](#caveats)

---

## Setup

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/warith-harchaoui/yt-helper.git@v1.1.0
```

Brings in `os-helper` / `audio-helper` / `video-helper` automatically.
You still need `yt-dlp` + `ffmpeg` on PATH (see README).

## Downloads (to disk)

The original `yt-helper` surface: pull a file to local storage.

```python
yth.download_video("https://www.youtube.com/watch?v=YE7VzlLtp-4", "bunny.mp4")
yth.download_audio("https://www.youtube.com/watch?v=YE7VzlLtp-4", "bunny.mp3")
yth.download_thumbnail("https://www.youtube.com/watch?v=YE7VzlLtp-4", "bunny.jpg")

# Cheap metadata probe (no download)
meta = yth.video_url_meta_data("https://www.youtube.com/watch?v=YE7VzlLtp-4")
print(meta["title"], meta["duration"])
```

## Stream Catalog & Picker

Where `download_*` writes a file, the catalog / picker functions hand
you a **direct media URL** + headers so a downstream decoder (PyAV /
ffmpeg / `video_helper.extract_frames`) can read it without re-going
through yt-dlp.

```python
# Enumerate every video format yt-dlp finds.
streams = yth.list_video_streams("https://www.youtube.com/watch?v=YE7VzlLtp-4")
for s in streams[:5]:
    print(f"{s['format_id']:6} {s['width']}x{s['height']} {s['fps']}fps "
          f"{s['vcodec']:14} {s['ext']:6} ~{s['vbr_kbps']:.0f} kbps")
# 160     256x144   30.0 avc1.42c00c   mp4    ~  110 kbps
# 278     256x144   30.0 vp09.00.11... webm   ~  102 kbps
# ...

# Pick the one matching your constraints — best yt-dlp candidate among matches.
pick = yth.pick_video_stream(
    "https://www.youtube.com/watch?v=YE7VzlLtp-4",
    prefer_codec="h264",   # also matches "avc1.xxx"
    prefer_format="mp4",
    max_fps=30,
)
# pick is a VideoStreamInfo:
#   {"format_id": "22", "url": "https://...mp4", "headers": {...},
#    "width": 1280, "height": 720, "fps": 30.0, "vcodec": "avc1.64001F",
#    "acodec": "mp4a.40.2", "is_live": False, ...}
```

**Note on audio**: a parallel audio catalog / picker intentionally lives
in **podcast-helper** (single owner for audio PCM streaming), not here.

## Direct-URL Resolver

When you don't need the catalog and just want **one** ffmpeg-ready URL:

```python
out = yth.resolve_direct_url(
    "https://www.youtube.com/watch?v=YE7VzlLtp-4",
    prefer="video",   # or "audio" for the cheapest audio-only path
)
# {"url": "https://...", "container": "mp4", "is_live": False,
#  "headers": {"User-Agent": "...", ...}}
```

Coarser than `pick_video_stream` (no codec / format / fps filtering),
but a single call.

## Composing with video-helper

The whole point of the catalog/picker: feed the direct URL + headers to
`video_helper.extract_frames` and decode without re-fetching the page.

```python
import video_helper as vh

pick = yth.pick_video_stream("https://www.youtube.com/watch?v=YE7VzlLtp-4",
                             prefer_codec="h264", max_fps=30)

for frame in vh.extract_frames(
    pick["url"],
    # http_headers=pick["headers"],   # ← coming in video-helper v1.5.0
    start_instant=10.0, end_instant=20.0,
    frame_interval=1.0,
    destination="torch", device="mps", batch_size=10, layout="image",
):
    # frame.shape == (10, 3, H, W), RGB uint8, on MPS
    embeddings = model(frame)
```

> **Heads-up**: passing `http_headers=` to `extract_frames` lands in
> video-helper v1.5.0. Until then, plain `http://` / `https://` URLs
> work fine for most yt-dlp-resolved YouTube videos, but live streams
> and members-only / age-gated content will 403 without the headers.

A convenience wrapper **`yth.extract_frames_stream(url, ...)`** that
hides the picker + delegates is planned for yt-helper v1.2.0, after the
`http_headers=` support lands.

## Branding — engagement metadata without API keys

`yt_helper.branding` extracts public engagement signals using yt-dlp's
own metadata dict — **no Google Data API, no Vimeo API, no OAuth,
no quota**.

```python
# One-video snapshot
meta = yth.video_engagement("https://www.youtube.com/watch?v=YE7VzlLtp-4")
print(meta["view_count"], meta["like_count"], meta["comment_count"])
print(meta["kind"])   # "short" / "long" / "live"

# Channel snapshot — subs, total views, video count
ch = yth.channel_info("https://www.youtube.com/@Blender")
print(f"{ch['title']}: {ch['follower_count']:,} subscribers, "
      f"{ch['video_count']:,} videos")

# Channel video list with per-video engagement (paginated, slow due to per-vid fetch)
videos = yth.channel_videos(
    "https://www.youtube.com/@Blender",
    max_videos=20,
    include_shorts=True,
    include_lives=False,
)
for v in videos:
    print(f"{v['upload_date']}  {v['view_count']:>10,} views  {v['title']}")

# Batched engagement across a list of URLs — tolerant (bad URLs → _error stub)
batch = yth.engagement_batch([url1, url2, url3])
for entry in batch:
    if "_error" in entry:
        print(f"skip {entry['url']}: {entry['_error']}")
    else:
        print(entry["title"], entry["view_count"])
```

**Normalised schema** (same fields whether the source is YouTube,
Vimeo, DailyMotion, or Twitch VOD):

```
id, url, title, description, upload_date (ISO YYYY-MM-DD),
duration_seconds, view_count, like_count, comment_count,
channel, channel_id, channel_url, channel_follower_count,
tags, categories, thumbnail, availability, live_status,
extractor, kind  # "short" / "long" / "live"
```

## Subtitles, Comments, Channels

```python
# Auto-subtitles → {lang: path_to_vtt}
subs = yth.video_subtitles(
    "https://www.youtube.com/watch?v=YE7VzlLtp-4",
    output_dir="captions",
    langs=("fr", "en"),
    auto_only=True,
)
# {"en": "captions/YE7VzlLtp-4.en.vtt"}

# Comments — YouTube increasingly requires browser cookies for comment threads.
comments = yth.video_comments(
    "https://www.youtube.com/watch?v=YE7VzlLtp-4",
    max_count=50,
    cookies_from_browser="firefox",   # or "chrome" / "safari" — read your active session
)
for c in comments[:3]:
    print(f"@{c['author']} ({c['like_count']} ♥): {c['text'][:80]}")

# Heuristic: is this a Short / vertical clip?
yth.is_short(yth.video_engagement(url))   # True / False
```

## Caveats

- **URL expiration** — Direct media URLs from yt-dlp expire (typically
  1-6 h for YouTube). For long-running jobs, re-resolve periodically
  or use `download_video` to materialize a local file.
- **Live streams** — `pick["is_live"] == True` and `pick["url"]` is
  typically an HLS `.m3u8` manifest. ffmpeg / PyAV handle these
  natively but: no seek backwards, no `frame_indices` / `frame_times`
  semantics, and hwaccel can be flaky with chunked HLS. The future
  `extract_frames_stream` will refuse `speed != 1.0` for live (you
  can't fast-forward past the live edge).
- **yt-dlp freshness** — YouTube rotates its signature scheme often.
  `yth.ensure_recent_ytdlp(min_version="2024.12.23")` warns when your
  installed yt-dlp is too old; `pip install -U yt-dlp` fixes most
  "broken decryption" errors.
- **Authentication** — Members-only / age-gated / private videos need
  cookies. Pass `cookies_from_browser="firefox"` (or `"chrome"` /
  `"safari"`) to the catalog / picker / branding functions; yt-dlp
  reads the active browser session.
- **Comments scraping** — YouTube comment threads almost always need
  `cookies_from_browser` now. Without it you'll usually get an empty
  list or a 403.
