"""
YT Helper

This module provides a set of utility functions to download videos, audio, and thumbnails
from URLs like YouTube, Vimeo, or DailyMotion using yt-dlp, and perform post-processing tasks
such as converting or merging media files with ffmpeg.

Dependencies
- yt-dlp
- ffmpeg
- PIL (Python Imaging Library)
- os_helper (custom utility for OS tasks)
- audio_helper (custom audio processing utility)
- video_helper (custom video processing utility)

Authors:
- Warith Harchaoui, https://harchaoui.org/warith
- Mohamed Chelali, https://mchelali.github.io
- Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

# Specify the public API of this module using __all__
__all__ = [
    "default_ytdlp_options",
    "video_url_meta_data",
    "is_valid_video_url",
    "download_thumbnail",
    "download_audio",
    "download_video",
    "download_bad_video_with_good_sound",
]


from .main import (
    default_ytdlp_options,
    video_url_meta_data,
    is_valid_video_url,
    download_thumbnail,
    download_audio,
    download_video,
    download_bad_video_with_good_sound,
)
