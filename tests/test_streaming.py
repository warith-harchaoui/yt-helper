"""Integration tests for yt_helper.streaming (catalog + picker + URL resolver).

All tests hit live yt-dlp extractors and require network. Marked
``integration`` and skipped by default; run with ``pytest -m integration``.

Test URLs are chosen for stability — Big Buck Bunny on YouTube is a
canonical "always available" sample. If YouTube changes its rate limiting,
tests may need a `cookies_from_browser` parameter.
"""

import os_helper as osh
import pytest

from yt_helper import (
    DirectMediaURL,
    VideoStreamInfo,
    list_video_streams,
    pick_video_stream,
    resolve_direct_url,
)

osh.verbosity(0)
pytestmark = pytest.mark.integration


# Stable, long-standing public video (Blender's Big Buck Bunny on YouTube).
SAMPLE_URL = "https://www.youtube.com/watch?v=YE7VzlLtp-4"


# ---------------------------------------------------------------------------
# resolve_direct_url (existed pre-v1.1)
# ---------------------------------------------------------------------------


def test_resolve_direct_url_video():
    out: DirectMediaURL = resolve_direct_url(SAMPLE_URL, prefer="video")
    assert out["url"].startswith("http")
    assert isinstance(out["headers"], dict)
    assert isinstance(out["is_live"], bool)
    assert out["container"] in {"mp4", "webm", "hls", "dash", "mov", "m4a"}


def test_resolve_direct_url_audio():
    out = resolve_direct_url(SAMPLE_URL, prefer="audio")
    assert out["url"].startswith("http")


# ---------------------------------------------------------------------------
# list_video_streams
# ---------------------------------------------------------------------------


def test_list_video_streams_returns_non_empty():
    streams = list_video_streams(SAMPLE_URL)
    assert len(streams) > 0
    # First entry should look like a complete VideoStreamInfo.
    s = streams[0]
    for key in ("format_id", "url", "headers", "ext", "container",
                "vcodec", "acodec", "width", "height", "fps",
                "vbr_kbps", "filesize_bytes", "is_live",
                "protocol", "language", "note"):
        assert key in s, f"missing key: {key}"
    # All entries are video (no audio-only formats leak through).
    for s in streams:
        assert s["vcodec"] != "none", f"unexpected audio-only: {s['format_id']}"


def test_list_video_streams_filter_combined_only():
    """include_video_only=False should keep only formats that have audio."""
    streams = list_video_streams(SAMPLE_URL, include_video_only=False)
    for s in streams:
        assert s["acodec"] != "none"


def test_list_video_streams_filter_video_only():
    """include_combined=False should keep only DASH-style video-only formats."""
    streams = list_video_streams(SAMPLE_URL, include_combined=False)
    # Most YouTube videos have several video-only DASH formats.
    if streams:
        for s in streams:
            assert s["acodec"] == "none"


# ---------------------------------------------------------------------------
# pick_video_stream
# ---------------------------------------------------------------------------


def test_pick_video_stream_no_constraints():
    pick = pick_video_stream(SAMPLE_URL)
    assert isinstance(pick, dict)
    assert pick["url"].startswith("http")
    # No constraints → best yt-dlp candidate (last in catalog).
    catalog = list_video_streams(SAMPLE_URL)
    assert pick["format_id"] == catalog[-1]["format_id"]


def test_pick_video_stream_prefer_format_mp4():
    pick = pick_video_stream(SAMPLE_URL, prefer_format="mp4")
    assert pick["ext"] == "mp4"


def test_pick_video_stream_max_fps_caps_choice():
    pick = pick_video_stream(SAMPLE_URL, max_fps=30.0)
    assert pick["fps"] <= 30.0


def test_pick_video_stream_impossible_constraint_raises():
    with pytest.raises(ValueError, match="No video stream matches"):
        # No video stream is going to satisfy a contradictory codec.
        pick_video_stream(SAMPLE_URL, prefer_codec="this-codec-does-not-exist")


def test_pick_video_stream_prefer_codec_h264():
    """h264 should match both 'avc1' and 'h264' codec names."""
    pick = pick_video_stream(SAMPLE_URL, prefer_codec="h264")
    # yt-dlp returns "avc1.xxxxxx" — our normaliser equates that with h264.
    assert "avc1" in pick["vcodec"].lower() or "h264" in pick["vcodec"].lower()
