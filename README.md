# YT Helper

`YT Helper` belongs to a collection of libraries called `AI Helpers` developed for building Artificial Intelligence.

[🕸️ AI Helpers](https://harchaoui.org/warith/ai-helpers)

[![logo](assets/logo.png)](https://harchaoui.org/warith/ai-helpers)

YT Helper is a Python library that provides utility functions for downloading videos, audio, and thumbnails from platforms like YouTube, Vimeo, and DailyMotion using `yt-dlp`.
It also supports post-processing tasks such as converting or merging media files with `ffmpeg`.

# Installation

## Install Package

We recommend using Python environments. Check this link if you're unfamiliar with setting one up:

[🥸 Tech tips](https://harchaoui.org/warith/4ml/#install)

### Install `yt-dlp` and `ffmpeg`

To install YT Helper, you must install the following dependencies:

- For macOS 🍎
  
Get [brew](https://brew.sh) and install the necessary packages:
```bash
brew install yt-dlp
brew install ffmpeg
```

- For Ubuntu 🐧
```bash
sudo apt install yt-dlp
sudo apt install ffmpeg
```

- For Windows 🪟
  - `yt-dlp`: Download [yt-dlp from its repository](https://github.com/yt-dlp/yt-dlp) and follow the instructions for your system.

  - `ffmpeg`: Go to the [FFmpeg website](https://ffmpeg.org/download.html) and follow the instructions for downloading FFmpeg. You'll need to manually add FFmpeg to your system PATH.

## Install `YT Helper`:
```bash
pip install --force-reinstall --no-cache-dir git+https://github.com/warith-harchaoui/yt-helper.git@v1.1.0
```

# Usage

For the full catalog of recipes (downloads, stream catalog / picker, direct-URL
resolver, composing with `video-helper`, branding metadata, subtitles &
comments), see [📋 EXAMPLES.md](EXAMPLES.md).

Quick start — download a video, extract metadata, and download the audio:

```python
import yt_helper as yth
import video_helper as vh
import audio_helper as ah
import os_helper as osh
import os

osh.verbosity(0)

# Example YouTube URL
youtube_url = "https://www.youtube.com/watch?v=YE7VzlLtp-4"

folder = "yt_tests"
os.makedirs(folder, exist_ok=True)

# Download a video
video = "big-buck-bunny.mp4"
video = os.path.join(folder, video)
yth.download_video(youtube_url, video)

# Extract metadata from the video URL
metadata = yth.video_url_meta_data(youtube_url)
print(metadata["title"])
# Big Buck Bunny

print(metadata["duration"])
# 597

print(metadata["description"])
# Big Buck Bunny tells the story of a giant rabbit with a heart bigger than himself. When one sunny day three rodents rudely harass him, something snaps... and the rabbit ain't no bunny anymore! In the typical cartoon tradition he prepares the nasty rodents a comical revenge.
# 
# Licensed under the Creative Commons Attribution license
# 
# http://www.bigbuckbunny.org/

print(metadata["channel"])
# Blender

details = vh.video_dimensions(video)
print(details)
# {'width': 1280, 'height': 720, 'duration': 596.458, 'frame_rate': 24.0, 'has_sound': True}

# Download the audio from the video
audio = "big-buck-bunny.mp3"
audio = os.path.join(folder, audio)
yth.download_audio(youtube_url, audio)

audio, sample_rate = ah.load_audio(audio)
print(sample_rate)
# 44100
```

# Legal and Ethical Use

YT Helper is a thin wrapper around `yt-dlp` and `ffmpeg`. You are responsible for how you use it. Only download or process media that you own, that is in the public domain or under a permissive license (e.g. Creative Commons), or for which you have explicit permission from the rights holder. Respect each platform's Terms of Service and any applicable copyright, privacy, and data-protection laws in your jurisdiction. The authors provide this library for legitimate uses such as personal archiving, accessibility, research, and content you have rights to — not for circumventing access controls or redistributing copyrighted material.

# Features

**Downloads (to disk)** — `yt_helper.main`
- `download_video(url, output_path)` / `download_audio(url, output_path)` / `download_thumbnail(url, output_path)`.
- `video_url_meta_data(url)` / `is_valid_video_url(url)` for cheap metadata probes.
- `default_ytdlp_options(verbose, ...)` for customisable yt-dlp options.

**Stream catalog & direct-URL resolution** — `yt_helper.streaming`
- `resolve_direct_url(url, prefer="audio"|"video")` → quick "give me one direct ffmpeg-ready URL".
- `list_video_streams(url)` → enumerate every video format yt-dlp finds (codec, resolution, fps, bitrate, …).
- `pick_video_stream(url, prefer_codec=, prefer_format=, max_fps=, language=, cookies_from_browser=)` → constrained picker, returns one `VideoStreamInfo` ready to feed `video_helper.extract_frames`.
- Audio stream catalog / picker intentionally lives in **podcast-helper** (single owner for audio PCM streaming).

**No-API engagement metadata** — `yt_helper.branding`
- `channel_info(url)` / `channel_videos(url, max_videos, include_shorts, include_lives)` — channel snapshot + paginated video list with normalised engagement metrics, cross-platform schema.
- `video_engagement(url)` / `engagement_batch([urls])` — per-video views / likes / comments / channel follower count, tolerant batched variant.
- `video_subtitles(url, output_dir, langs=("fr","en"))` — auto-subtitle download.
- `video_comments(url, max_count, cookies_from_browser="firefox"|"chrome"|...)` — comments sample.
- `is_short(meta)` / `ensure_recent_ytdlp(min_version)` — helpers.
- Built on yt-dlp's public metadata only — **no Google Data API, no Vimeo API, no OAuth, no quota.**

# Author
 - [Warith HARCHAOUI](https://harchaoui.org/warith)

# Acknowledgements
Special thanks to [Mohamed Chelali](https://mchelali.github.io) and [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug) for fruitful discussions.
