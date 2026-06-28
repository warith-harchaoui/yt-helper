"""
YT Helper

Utilities for downloading videos, audio, thumbnails, resolving direct
media URLs, and pulling public engagement metadata — from YouTube, Vimeo,
DailyMotion, Twitch VOD, and any other site `yt-dlp` supports.

Modules
-------
- ``main``       : download helpers (videos / audio / thumbnails) and
                   metadata extraction.
- ``streaming``  : URL resolver that turns a user-facing page URL into a
                   direct media URL (with the right headers / cookies) so
                   an ffmpeg-based reader can consume it without going
                   through yt-dlp again. Pure resolution — no PCM
                   decoding (that's ``podcast_helper``'s job).
- ``branding``   : no-API engagement helpers (channel info, video lists
                   with normalised metrics, subtitles, comments). Built
                   on yt-dlp's public metadata — no Google Data API,
                   no Vimeo API, no OAuth, no quota.

Dependencies
- yt-dlp
- ffmpeg (on PATH)
- os-helper / audio-helper / video-helper

Author:
- Warith HARCHAOUI, https://harchaoui.org/warith
"""

__all__ = [
    # main — download helpers
    "default_ytdlp_options",
    "video_url_meta_data",
    "is_valid_video_url",
    "download_thumbnail",
    "download_audio",
    "download_video",
    # streaming — URL resolver + catalog/picker
    "resolve_direct_url",
    "DirectMediaURL",
    "list_video_streams",
    "pick_video_stream",
    "VideoStreamInfo",
    # branding — engagement / channel helpers (no Data / Analytics API)
    "channel_info",
    "channel_videos",
    "video_engagement",
    "video_subtitles",
    "video_comments",
    "engagement_batch",
    "is_short",
    "ensure_recent_ytdlp",
]


from .main import (
    default_ytdlp_options,
    video_url_meta_data,
    is_valid_video_url,
    download_thumbnail,
    download_audio,
    download_video,
)

from .streaming import (
    DirectMediaURL,
    VideoStreamInfo,
    list_video_streams,
    pick_video_stream,
    resolve_direct_url,
)

from .branding import (
    channel_info,
    channel_videos,
    video_engagement,
    video_subtitles,
    video_comments,
    engagement_batch,
    is_short,
    ensure_recent_ytdlp,
)
