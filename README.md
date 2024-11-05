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
pip install --force-reinstall --no-cache-dir git+https://github.com/warith-harchaoui/yt-helper.gitv1.0.0
```

# Usage

Here’s an example of how to use YT Helper to download a video, extract metadata, and download the audio:

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

# Features
- *Video Downloading*: Download videos from platforms like YouTube, Vimeo, and DailyMotion using yt-dlp.
- *Audio Downloading*: Download the best available audio from videos.
- *Thumbnail Downloading*: Extract and save video thumbnails.
- *Video Metadata*: Retrieve metadata such as title, description, and duration without downloading the entire video.
- *Flexible yt-dlp Options*: Customize download options like format and verbosity using helper functions.

# Authors
 - [Warith Harchaoui](https://harchaoui.org/warith)
 - [Mohamed Chelali](https://mchelali.github.io)
 - [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug)
