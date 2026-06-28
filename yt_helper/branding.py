"""YT Helper — branding companion module.

Engagement / channel / comments / subtitles helpers for personal-branding
workflows that do **not** require Google Data API or Vimeo API keys.

These functions complement `yt_helper.main` (download utilities) with
public-metadata extraction useful to score a creator's track record:
    - channel-level snapshot (subscribers, total views, video count, title)
    - channel video list (paginated, with normalised engagement metadata)
    - single video engagement signals (views / likes / comments)
    - auto-subtitle download (returns a {lang: path} dict)
    - comments sample (cookies-from-browser optional for restricted threads)

All work for **YouTube, Vimeo, DailyMotion, Twitch VOD, and any other site
yt-dlp supports**, with one homogeneous return shape.

Anti-API rationale
------------------
Most "live engagement" numbers a personal-brand tool needs (view_count,
like_count, comment_count, channel_follower_count, duration, upload_date,
tags, description, thumbnail) are present in the public yt-dlp metadata for
unrestricted videos. No OAuth, no client_id, no quota. The Data API only
becomes necessary for **per-video retention curves** (Analytics API) and
**comments at scale** (the public commentThreads endpoint).

Author:
- Warith HARCHAOUI, https://harchaoui.org/warith
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yt_dlp


# ─── Internal helpers ────────────────────────────────────────────────────────

_SHORT_DURATION_THRESHOLD_SEC = 60


def _minimal_options(verbose: bool = False, **extra: Any) -> dict[str, Any]:
    """Bare-bones yt-dlp options for metadata extraction.

    Avoids the side-effects of `default_ytdlp_options` (which writes a
    timestamped cookie file). Suitable for read-only metadata work.
    """
    options: dict[str, Any] = {
        "quiet": not verbose,
        "no_warnings": not verbose,
        "skip_download": True,
        "extract_flat": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.5",
        },
    }
    options.update(extra)
    return options


def _safe_int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _safe_iso_date(yyyymmdd: Any) -> str:
    """Convert YYYYMMDD (yt-dlp `upload_date`) to ISO `YYYY-MM-DD`."""
    if not yyyymmdd:
        return ""
    s = str(yyyymmdd)
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s


def is_short(meta: dict[str, Any]) -> bool:
    """Heuristic — true if the entry looks like a Short / vertical clip.

    Looks at duration (≤ 60s), webpage_url (`/shorts/`), and #Shorts in title.
    """
    duration = _safe_int(meta.get("duration"))
    if 0 < duration <= _SHORT_DURATION_THRESHOLD_SEC:
        return True
    url = meta.get("webpage_url") or meta.get("url") or ""
    if "/shorts/" in url:
        return True
    text = f"{meta.get('title') or ''} {meta.get('description') or ''}".lower()
    if "#shorts" in text or "#short" in text:
        return True
    tags = [t.lower() for t in (meta.get("tags") or [])]
    return "shorts" in tags or "short" in tags


def _normalise_video_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Project a raw yt-dlp video entry into a homogeneous engagement dict.

    Same shape regardless of the source platform (YouTube / Vimeo /
    DailyMotion / Twitch VOD / …). See the module docstring for the full
    schema description.
    """
    duration = _safe_int(meta.get("duration"))
    return {
        "id": meta.get("id"),
        "url": meta.get("webpage_url") or meta.get("original_url") or meta.get("url"),
        "title": meta.get("title") or "",
        "description": meta.get("description") or "",
        "upload_date": _safe_iso_date(meta.get("upload_date")),
        "duration_seconds": duration,
        "view_count": _safe_int(meta.get("view_count")),
        "like_count": _safe_int(meta.get("like_count")),
        "comment_count": _safe_int(meta.get("comment_count")),
        "channel_id": meta.get("channel_id"),
        "channel_url": meta.get("channel_url"),
        "channel": meta.get("channel") or meta.get("uploader"),
        "channel_follower_count": _safe_int(meta.get("channel_follower_count")),
        "tags": meta.get("tags") or [],
        "categories": meta.get("categories") or [],
        "thumbnail": meta.get("thumbnail"),
        "availability": meta.get("availability"),
        "live_status": meta.get("live_status"),
        "extractor": meta.get("extractor") or meta.get("extractor_key"),
        "kind": "short" if is_short(meta) else ("live" if meta.get("live_status") == "is_live" else "long"),
    }


# ─── Public — channel-level ──────────────────────────────────────────────────

def channel_info(url: str, verbose: bool = False) -> dict[str, Any]:
    """Return one normalised dict describing the channel / creator page.

    Works with YouTube channel URLs (`/@handle`, `/channel/UC…`),
    Vimeo user pages, DailyMotion creators. Pulls subscriber count, channel
    title, description, total view count when available.
    """
    options = _minimal_options(verbose=verbose, extract_flat="in_playlist")
    with yt_dlp.YoutubeDL(options) as ydl:
        meta = ydl.extract_info(url, download=False)
    if not meta:
        return {}
    return {
        "id": meta.get("channel_id") or meta.get("id"),
        "url": meta.get("channel_url") or meta.get("webpage_url") or url,
        "title": meta.get("channel") or meta.get("uploader") or meta.get("title"),
        "handle": meta.get("uploader_id") or meta.get("channel_id"),
        "description": meta.get("description") or "",
        "follower_count": _safe_int(meta.get("channel_follower_count")),
        "video_count": _safe_int(meta.get("playlist_count") or len(meta.get("entries") or [])),
        "view_count_total": _safe_int(meta.get("view_count")),
        "extractor": meta.get("extractor") or meta.get("extractor_key"),
    }


def channel_videos(
    url: str,
    max_videos: int = 200,
    include_shorts: bool = True,
    include_lives: bool = False,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """List videos of a channel / creator page with per-video engagement metadata.

    For YouTube channels, walks the uploads playlist; for Vimeo / DailyMotion,
    walks the user page. Each entry is normalised to the same engagement
    schema (``id``, ``url``, ``title``, ``duration_seconds``, ``view_count``,
    ``like_count``, ``comment_count``, ``upload_date``, ``kind``, …).

    Two-pass strategy: a fast flat listing first (1 call), then per-video
    metadata fetch (1 call per video). The second pass is what makes
    ``view_count`` / ``like_count`` reliable — ``extract_flat`` returns
    IDs and sometimes ``view_count``, but rarely likes / comments.
    """
    # Pass 1: flat listing of IDs.
    flat_options = _minimal_options(
        verbose=verbose,
        extract_flat=True,
        playlistend=max_videos,
    )
    with yt_dlp.YoutubeDL(flat_options) as ydl:
        page = ydl.extract_info(url, download=False)
    entries = page.get("entries") or []

    # Pass 2: per-video metadata fetch (limited to the cap).
    full_options = _minimal_options(verbose=verbose, skip_download=True)
    detailed: list[dict[str, Any]] = []
    with yt_dlp.YoutubeDL(full_options) as ydl:
        for entry in entries[:max_videos]:
            if not entry:
                continue
            video_url = entry.get("url") or entry.get("webpage_url")
            if not video_url:
                continue
            try:
                meta = ydl.extract_info(video_url, download=False)
            except yt_dlp.utils.DownloadError as e:  # noqa: BLE001
                logging.debug("yt-helper: skip %s (%s)", video_url, e)
                continue
            if not meta:
                continue
            norm = _normalise_video_meta(meta)
            if not include_shorts and norm["kind"] == "short":
                continue
            if not include_lives and norm["kind"] == "live":
                continue
            detailed.append(norm)
    return detailed


# ─── Public — single-video ───────────────────────────────────────────────────

def video_engagement(url: str, verbose: bool = False) -> dict[str, Any]:
    """Single-video engagement snapshot. Returns the normalised dict shape."""
    options = _minimal_options(verbose=verbose)
    with yt_dlp.YoutubeDL(options) as ydl:
        meta = ydl.extract_info(url, download=False)
    if not meta:
        return {}
    return _normalise_video_meta(meta)


def video_subtitles(
    url: str,
    output_dir: str | Path,
    langs: Iterable[str] = ("fr", "en"),
    auto_only: bool = True,
    verbose: bool = False,
) -> dict[str, str]:
    """Download auto-generated (or manual) subtitles into `output_dir`.

    Returns a dict mapping language → absolute path of the saved `.vtt` file.
    Languages that aren't available are silently skipped.
    """
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    options = _minimal_options(
        verbose=verbose,
        writesubtitles=not auto_only,
        writeautomaticsub=auto_only,
        subtitleslangs=list(langs),
        subtitlesformat="vtt",
        skip_download=True,
        outtmpl=str(out_dir / "%(id)s.%(ext)s"),
    )
    with yt_dlp.YoutubeDL(options) as ydl:
        meta = ydl.extract_info(url, download=True)

    video_id = (meta or {}).get("id") or ""
    out: dict[str, str] = {}
    for lang in langs:
        candidate = out_dir / f"{video_id}.{lang}.vtt"
        if candidate.exists():
            out[lang] = str(candidate)
    return out


def video_comments(
    url: str,
    max_count: int = 100,
    cookies_from_browser: str | None = None,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Fetch comments via yt-dlp's `getcomments`.

    YouTube increasingly requires browser cookies for comment scraping. If
    `cookies_from_browser` is set (e.g. `"firefox"`, `"chrome"`, `"safari"`),
    yt-dlp will pull cookies from that browser's profile. On macOS this is the
    only reliable way to get YouTube comments today.

    Returns a list of normalised comment dicts: id, parent, author, text,
    like_count, timestamp.
    """
    extra: dict[str, Any] = {
        "getcomments": True,
        "extractor_args": {
            "youtube": {
                "max_comments": [str(max_count), "all", "all", "all"],
                "comment_sort": ["top"],
            }
        },
    }
    if cookies_from_browser:
        extra["cookiesfrombrowser"] = (cookies_from_browser,)

    options = _minimal_options(verbose=verbose, **extra)
    with yt_dlp.YoutubeDL(options) as ydl:
        meta = ydl.extract_info(url, download=False)

    comments = (meta or {}).get("comments") or []
    normalised: list[dict[str, Any]] = []
    for c in comments[:max_count]:
        if not isinstance(c, dict):
            continue
        normalised.append({
            "id": c.get("id"),
            "parent": c.get("parent"),
            "author": c.get("author"),
            "author_id": c.get("author_id"),
            "text": c.get("text"),
            "like_count": _safe_int(c.get("like_count")),
            "timestamp": c.get("timestamp"),
            "iso_date": _ts_to_iso(c.get("timestamp")),
            "is_favorited": bool(c.get("is_favorited")),
        })
    return normalised


def _ts_to_iso(ts: Any) -> str:
    """Render a Unix epoch as ``YYYY-MM-DDTHH:MM:SS+00:00`` (UTC), or ``""``.

    Uses timezone-aware ``datetime.fromtimestamp(..., tz=timezone.utc)``
    because :meth:`datetime.utcfromtimestamp` is deprecated in Python 3.12+.
    """
    if isinstance(ts, (int, float)) and ts > 0:
        try:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
        except (OSError, ValueError, OverflowError):
            return ""
    return ""


# ─── Convenience — multi-video batched engagement ────────────────────────────

def engagement_batch(urls: Iterable[str], verbose: bool = False) -> list[dict[str, Any]]:
    """Map a list of URLs to normalised engagement dicts, one per URL.

    Tolerant: bad URLs / unavailable videos are reported as `{"url": …,
    "_error": "..."}` rather than raising.
    """
    out: list[dict[str, Any]] = []
    options = _minimal_options(verbose=verbose)
    with yt_dlp.YoutubeDL(options) as ydl:
        for u in urls:
            try:
                meta = ydl.extract_info(u, download=False)
            except yt_dlp.utils.DownloadError as e:  # noqa: BLE001
                out.append({"url": u, "_error": str(e)[:200]})
                continue
            if not meta:
                out.append({"url": u, "_error": "empty metadata"})
                continue
            out.append(_normalise_video_meta(meta))
    return out


# ─── Convenience — ensure yt-dlp is fresh ────────────────────────────────────

def ensure_recent_ytdlp(min_version: str | None = None) -> str:
    """Return the installed yt-dlp version. Warn if older than `min_version`.

    YouTube changes its signature scheme roughly every quarter; an outdated
    yt-dlp is the #1 cause of failures. Callers that mind freshness can
    surface a warning early.
    """
    version = getattr(yt_dlp, "version", None)
    version_str = getattr(version, "__version__", None) or "unknown"
    if min_version and version_str != "unknown":
        try:
            installed = tuple(int(x) for x in re.findall(r"\d+", version_str)[:3])
            wanted = tuple(int(x) for x in re.findall(r"\d+", min_version)[:3])
            if installed < wanted:
                logging.warning(
                    "yt-helper: yt-dlp %s is older than %s — consider `pip install -U yt-dlp`.",
                    version_str, min_version,
                )
        except (ValueError, TypeError):
            pass
    return version_str
