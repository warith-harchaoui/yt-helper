"""
yt_helper.streaming
===================

Stream catalog, picker, and direct-URL resolution for
``yt-dlp``-supported sites. Does NOT decode anything — the resolved
URLs are meant to be consumed by:

- :mod:`video_helper.extract_frames` for video frames
- ``podcast_helper.iter_pcm`` (separate package) for audio PCM

What this module gives you, layered from low-level to high-level:

- :class:`VideoStreamInfo` — typed dict describing one video format.
- :func:`list_video_streams` — enumerate every video format yt-dlp
  finds for a URL (one entry per resolution / codec / container).
- :func:`pick_video_stream` — pick the single best video stream
  matching codec / format / fps / language constraints.
- :func:`resolve_direct_url` — quick "give me ONE direct URL ready
  for ffmpeg" (audio or video flavour). Coarser than ``pick_*``.

Audio stream catalog / picker intentionally NOT in this module — that
responsibility lives in ``podcast-helper`` so the audio decoding path
has a single owner.

Author
------
Warith HARCHAOUI — https://harchaoui.org/warith
"""

from __future__ import annotations

import logging
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


# ──────────────────────────────────────────────────────────────────────────
#  Video stream catalog + picker
#
#  Where ``resolve_direct_url`` is a quick "give me ONE direct URL"
#  helper, ``list_video_streams`` / ``pick_video_stream`` are the catalog
#  layer — they expose every video format yt-dlp knows about, normalised
#  into a homogeneous :class:`VideoStreamInfo` dict that consumers
#  (notably :mod:`video_helper.extract_frames`) can use directly.
# ──────────────────────────────────────────────────────────────────────────


class VideoStreamInfo(TypedDict):
    """One video format's metadata, normalised across extractors.

    Keys
    ----
    format_id : str
        yt-dlp's stable identifier for this format on this URL.
    url : str
        The direct media URL — ready for ffmpeg / PyAV.
    headers : dict[str, str]
        HTTP headers ffmpeg must send with the request (User-Agent,
        Referer, Cookie, …). Pass through to
        ``video_helper.extract_frames(http_headers=...)`` or to
        ffmpeg's ``-headers`` flag.
    ext : str
        File extension reported by yt-dlp (``"mp4"`` / ``"webm"`` / ``"m3u8"`` / …).
    container : str
        Normalised container hint (``"mp4"`` / ``"webm"`` / ``"hls"`` /
        ``"dash"``) — useful when the ext is ambiguous.
    vcodec : str
        Video codec (``"h264"`` / ``"vp9"`` / ``"av01"`` / ``"none"`` if
        audio-only — filtered out of this list).
    acodec : str
        Audio codec (``"none"`` for video-only formats — common on
        YouTube DASH, paired with a separate audio-only format).
    width, height : int
        Pixels. ``0`` if unknown (rare).
    fps : float
        Frames per second. ``0.0`` if unknown.
    vbr_kbps : float
        Estimated video bitrate in kbit/s. ``0.0`` if unknown.
    filesize_bytes : int
        Estimated file size in bytes. ``0`` if unknown (always 0 for live).
    is_live : bool
        True if this is a live stream (URL is an HLS / DASH manifest).
    protocol : str
        yt-dlp's protocol string (``"https"`` / ``"m3u8_native"`` /
        ``"http_dash_segments"`` / …).
    language : str | None
        Language code if the format carries an explicit one (rare for
        video; common for audio).
    note : str
        yt-dlp's ``format_note`` — typically a human-readable label
        (``"1080p60"``, ``"Premium"``, …).
    """

    format_id: str
    url: str
    headers: dict[str, str]
    ext: str
    container: str
    vcodec: str
    acodec: str
    width: int
    height: int
    fps: float
    vbr_kbps: float
    filesize_bytes: int
    is_live: bool
    protocol: str
    language: str | None
    note: str


def _container_for(ext: str, url: str) -> str:
    """Normalise extension into a container hint (same logic as resolve_direct_url)."""
    if ext == "m3u8" or ".m3u8" in url:
        return "hls"
    if ext == "mpd" or ".mpd" in url:
        return "dash"
    return ext or "mp4"


def _to_video_stream_info(fmt: dict[str, Any], default_headers: dict[str, str], is_live: bool) -> VideoStreamInfo:
    """Project one yt-dlp ``formats[i]`` entry into a VideoStreamInfo."""
    url = fmt.get("url") or ""
    ext = fmt.get("ext") or "mp4"
    # Per-format headers fall back to the info-level headers (yt-dlp
    # sometimes hangs them at the top level, sometimes per format).
    headers = dict(fmt.get("http_headers") or default_headers or {})
    return {
        "format_id": str(fmt.get("format_id") or ""),
        "url": url,
        "headers": headers,
        "ext": ext,
        "container": _container_for(ext, url),
        "vcodec": str(fmt.get("vcodec") or "none"),
        "acodec": str(fmt.get("acodec") or "none"),
        "width": int(fmt.get("width") or 0),
        "height": int(fmt.get("height") or 0),
        "fps": float(fmt.get("fps") or 0.0),
        "vbr_kbps": float(fmt.get("vbr") or fmt.get("tbr") or 0.0),
        "filesize_bytes": int(fmt.get("filesize") or fmt.get("filesize_approx") or 0),
        "is_live": is_live,
        "protocol": str(fmt.get("protocol") or ""),
        "language": fmt.get("language"),
        "note": str(fmt.get("format_note") or ""),
    }


def _extract_info_for_catalog(
    url: str,
    cookies_from_browser: str | None,
    verbose: bool,
) -> dict[str, Any]:
    """Run ``yt-dlp`` in read-only mode and return the full info dict."""
    ydl_opts: dict[str, Any] = {
        "skip_download": True,
        "quiet": not verbose,
        "no_warnings": not verbose,
        "extract_flat": False,
    }
    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info is None:
        raise RuntimeError(f"yt-dlp could not extract info for URL: {url!r}")
    if "entries" in info and info["entries"]:
        info = info["entries"][0]
    return info


def list_video_streams(
    url: str,
    *,
    include_video_only: bool = True,
    include_combined: bool = True,
    cookies_from_browser: str | None = None,
    verbose: bool = False,
) -> list[VideoStreamInfo]:
    """Enumerate every video format yt-dlp finds for this URL.

    Results are ordered by yt-dlp's quality ranking (best last). Pure
    video-only formats and combined (video + audio) formats are both
    included by default — adjust with the boolean flags.

    Parameters
    ----------
    url : str
        Any URL yt-dlp can extract.
    include_video_only : bool, optional
        Keep formats with ``acodec="none"`` (DASH-style streams that
        need a separate audio mux). Default True.
    include_combined : bool, optional
        Keep formats with both video and audio (legacy progressive
        streams; common on Vimeo, rare on YouTube high-quality). Default True.
    cookies_from_browser : str, optional
        Pass through to yt-dlp's ``--cookies-from-browser`` (e.g.
        ``"firefox"`` / ``"chrome"`` / ``"safari"``) for age-gated or
        login-required content.
    verbose : bool, optional
        Echo yt-dlp's output to stderr (off by default).

    Returns
    -------
    list[VideoStreamInfo]
        Possibly empty if the URL has no video (audio-only podcast,
        for example).

    Raises
    ------
    RuntimeError
        If yt-dlp could not extract info at all (private video,
        geo-blocked without bypass, removed, …).
    """
    info = _extract_info_for_catalog(url, cookies_from_browser, verbose)
    is_live = bool(info.get("is_live") or info.get("live_status") == "is_live")
    default_headers = dict(info.get("http_headers") or {})

    out: list[VideoStreamInfo] = []
    for fmt in info.get("formats") or []:
        vcodec = fmt.get("vcodec") or "none"
        acodec = fmt.get("acodec") or "none"
        if vcodec == "none":
            continue  # audio-only — out of scope here
        is_combined = acodec != "none"
        if is_combined and not include_combined:
            continue
        if not is_combined and not include_video_only:
            continue
        out.append(_to_video_stream_info(fmt, default_headers, is_live))
    return out


def pick_video_stream(
    url: str,
    *,
    prefer_codec: str | None = None,
    prefer_format: str | None = None,
    max_fps: float | None = None,
    language: str | None = None,
    include_video_only: bool = True,
    include_combined: bool = True,
    cookies_from_browser: str | None = None,
    verbose: bool = False,
) -> VideoStreamInfo:
    """Pick a single best video stream matching the given constraints.

    Among the catalog returned by :func:`list_video_streams`, applies
    each non-None constraint as a hard filter, then returns the
    highest-ranked remaining candidate (yt-dlp's native order — typically
    sorts by height × bitrate).

    Parameters
    ----------
    url : str
        Source URL (any yt-dlp-supported site).
    prefer_codec : str, optional
        Substring match against ``vcodec`` (``"h264"`` matches both
        ``"avc1.640028"`` and ``"h264"`` once normalised; ``"vp9"``
        matches ``"vp09.00.40.08"``; ``"av1"`` matches ``"av01..."``).
    prefer_format : str, optional
        Equality match against ``ext`` (``"mp4"`` / ``"webm"``).
    max_fps : float, optional
        Drop formats with ``fps > max_fps``.
    language : str, optional
        Equality match against the format's ``language`` (rarely set
        for video — primarily useful when the source carries multi-track
        video).
    include_video_only, include_combined : bool, optional
        See :func:`list_video_streams`.
    cookies_from_browser, verbose : same as :func:`list_video_streams`.

    Returns
    -------
    VideoStreamInfo
        The chosen stream.

    Raises
    ------
    RuntimeError
        If yt-dlp can't extract the URL.
    ValueError
        If no stream matches the constraints (the catalog itself was
        non-empty, but every entry got filtered out).
    """
    catalog = list_video_streams(
        url,
        include_video_only=include_video_only,
        include_combined=include_combined,
        cookies_from_browser=cookies_from_browser,
        verbose=verbose,
    )
    if not catalog:
        raise ValueError(f"No video streams available for URL: {url!r}")

    def _matches(s: VideoStreamInfo) -> bool:
        if prefer_codec is not None:
            # Normalise common aliases: "h264" ↔ "avc1", "av1" ↔ "av01".
            wanted = prefer_codec.lower().replace("avc1", "h264").replace("av01", "av1")
            actual = s["vcodec"].lower().replace("avc1", "h264").replace("av01", "av1")
            if wanted not in actual:
                return False
        if prefer_format is not None and s["ext"].lower() != prefer_format.lower():
            return False
        if max_fps is not None and s["fps"] > max_fps:
            return False
        if language is not None and (s["language"] or "").lower() != language.lower():
            return False
        return True

    matching = [s for s in catalog if _matches(s)]
    if not matching:
        raise ValueError(
            f"No video stream matches constraints "
            f"(prefer_codec={prefer_codec!r}, prefer_format={prefer_format!r}, "
            f"max_fps={max_fps!r}, language={language!r}) for URL: {url!r}. "
            f"Catalog had {len(catalog)} candidate(s); call list_video_streams() "
            f"to inspect."
        )

    # yt-dlp orders best last in `formats`; list_video_streams preserves that.
    chosen = matching[-1]
    logging.info(
        "yt-helper: picked %s (%dx%d %s %s @ %.0ffps, ~%.0f kbps) from %d candidate(s)",
        chosen["format_id"], chosen["width"], chosen["height"],
        chosen["vcodec"], chosen["ext"], chosen["fps"], chosen["vbr_kbps"],
        len(matching),
    )
    return chosen
