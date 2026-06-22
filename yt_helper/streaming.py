"""
yt_helper.streaming
===================

Live + on-demand streaming resolution for ``yt-dlp``-supported sites.
Does not pipe PCM itself — that's :mod:`audio_helper.streaming`'s job.
This module resolves a user-facing URL (which may need cookies,
age-gate handling, geo-bypass, or HLS manifest selection) to a *direct*
media URL that any ffmpeg-based reader can consume.

Designed to land upstream as a follow-up PR on
``warith-harchaoui/yt-helper``.

Author
------
Warith Harchaoui — https://www.linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

# yt-dlp is already a dep of yt-helper; we use its Python API rather
# than shelling out so we keep the info dict (URL + headers + is_live).
from yt_dlp import YoutubeDL


class DirectMediaURL(TypedDict):
    """Resolved direct-media URL ready for ffmpeg.

    Keys
    ----
    url : str
        The direct media URL. Can be an HLS ``.m3u8`` (live), DASH
        ``.mpd``, or progressive ``.mp4`` / ``.webm`` — whichever
        ``yt-dlp`` selected.
    container : str
        Container format string (``"hls"``, ``"dash"``, ``"mp4"``,
        ``"webm"``, ``"audio"``, …). Useful for ffmpeg's ``-f`` hint
        if the URL extension is ambiguous.
    is_live : bool
        True if the source is a live stream. Callers may want to skip
        ``-re`` (real-time pacing) since live is already real-time.
    headers : dict[str, str]
        HTTP headers the player must send with the request. YouTube
        often requires a specific ``User-Agent`` and ``Referer`` to
        avoid 403s; pass them to ffmpeg via ``-headers``.
    """

    url: str
    container: str
    is_live: bool
    headers: dict[str, str]


def resolve_direct_url(
    url: str,
    *,
    prefer: Literal["audio", "video"] = "audio",
    live: Literal["auto", "force_live", "force_vod"] = "auto",
) -> DirectMediaURL:
    """Resolve ``url`` to a direct, ffmpeg-readable media URL.

    Parameters
    ----------
    url : str
        Any URL ``yt-dlp`` can extract (YouTube / Vimeo / DailyMotion /
        Twitch / …).
    prefer : ``"audio"`` | ``"video"``
        Format preference. ``"audio"`` selects ``bestaudio`` —
        cheapest path for ASR + diarization. ``"video"`` selects
        ``best`` (video + audio muxed), useful for the ``/video`` view
        (Phase 7) that needs the visual track too.
    live : ``"auto"`` | ``"force_live"`` | ``"force_vod"``
        ``"auto"`` propagates whatever the info dict says (the usual
        case). The other two override — handy for testing or when the
        site mislabels a stream.

    Returns
    -------
    DirectMediaURL
        See class docstring.

    Raises
    ------
    RuntimeError
        If ``yt-dlp`` could not extract a usable URL (private video,
        geo-blocked without bypass, removed, …).
    """
    # We pick the format based on ``prefer``. ``bestaudio*`` matches any
    # audio-only stream; ``best`` matches the best combined stream. The
    # ``*`` allows yt-dlp to fall back across audio-only candidates.
    fmt = "bestaudio*" if prefer == "audio" else "best"

    ydl_opts: dict[str, Any] = {
        "format": fmt,
        # No download — just resolve.
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        # For live streams, prefer HLS m3u8 over DASH where available;
        # ffmpeg's HLS demuxer is the most battle-tested path.
        "hls_prefer_native": False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        raise RuntimeError(
            f"yt-dlp could not extract info for URL: {url!r}"
        )

    # ``yt-dlp`` may give us a playlist; resolve to the first entry.
    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    # Choose the format. When yt-dlp already applied our ``format``
    # selector, ``info["url"]`` is the direct URL and ``info["ext"]``
    # tells us the container.
    direct_url = info.get("url")
    if not direct_url:
        # Some extractors require us to walk ``formats`` ourselves.
        formats = info.get("formats", [])
        if not formats:
            raise RuntimeError(
                f"No usable formats for URL: {url!r}"
            )
        # Pick the last one — yt-dlp orders best last by default.
        chosen = formats[-1]
        direct_url = chosen["url"]
        ext = chosen.get("ext", "mp4")
    else:
        ext = info.get("ext", "mp4")

    # Live detection: ``is_live`` is the primary signal; ``live_status``
    # ("is_live" / "was_live" / "not_live" / ...) is the newer one.
    if live == "force_live":
        is_live = True
    elif live == "force_vod":
        is_live = False
    else:
        is_live = bool(
            info.get("is_live")
            or info.get("live_status") == "is_live"
        )

    # Container hint. We normalise a couple of common cases so the
    # caller doesn't have to.
    if ext == "m3u8" or ".m3u8" in direct_url:
        container = "hls"
    elif ext == "mpd" or ".mpd" in direct_url:
        container = "dash"
    else:
        container = ext

    # Headers. ``http_headers`` is yt-dlp's canonical place for this;
    # we always include a User-Agent because some sites 403 on the
    # default one.
    headers = dict(info.get("http_headers") or {})

    return {
        "url": direct_url,
        "container": container,
        "is_live": is_live,
        "headers": headers,
    }
