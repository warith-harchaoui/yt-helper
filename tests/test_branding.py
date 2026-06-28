"""Integration tests for yt_helper.branding (engagement metadata).

Marked ``integration`` (network + yt-dlp + sometimes site-specific
quirks). Skipped by default; run with ``pytest -m integration``.
"""

import os_helper as osh
import pytest

from yt_helper import (
    channel_info,
    channel_videos,
    engagement_batch,
    ensure_recent_ytdlp,
    is_short,
    video_engagement,
)

osh.verbosity(0)
pytestmark = pytest.mark.integration


SAMPLE_VIDEO = "https://www.youtube.com/watch?v=YE7VzlLtp-4"  # Big Buck Bunny
SAMPLE_CHANNEL = "https://www.youtube.com/@Blender"           # the channel that uploaded it


# ---------------------------------------------------------------------------
# is_short — pure heuristic, no network needed but kept here for cohesion
# ---------------------------------------------------------------------------


def test_is_short_by_duration():
    assert is_short({"duration": 30}) is True
    assert is_short({"duration": 90}) is False


def test_is_short_by_url():
    assert is_short({"webpage_url": "https://www.youtube.com/shorts/abc123"}) is True


def test_is_short_by_hashtag():
    assert is_short({"title": "Funny clip #Shorts", "description": ""}) is True


def test_is_short_by_tag():
    assert is_short({"tags": ["shorts", "comedy"]}) is True


# ---------------------------------------------------------------------------
# video_engagement
# ---------------------------------------------------------------------------


def test_video_engagement_homogeneous_schema():
    meta = video_engagement(SAMPLE_VIDEO)
    assert isinstance(meta, dict)
    # Schema invariants — every field present even if 0 / "" / None.
    for key in ("id", "url", "title", "duration_seconds",
                "view_count", "like_count", "comment_count",
                "channel", "channel_url", "thumbnail", "kind"):
        assert key in meta, f"missing key: {key}"
    assert meta["title"]
    assert meta["duration_seconds"] > 0
    assert meta["view_count"] > 0
    assert meta["kind"] in {"short", "long", "live"}


# ---------------------------------------------------------------------------
# channel_info / channel_videos
# ---------------------------------------------------------------------------


def test_channel_info_returns_normalised_fields():
    info = channel_info(SAMPLE_CHANNEL)
    assert isinstance(info, dict)
    for key in ("id", "url", "title", "description",
                "follower_count", "video_count", "extractor"):
        assert key in info, f"missing key: {key}"
    assert info["title"]
    assert info["follower_count"] > 0
    assert info["extractor"]


def test_channel_videos_returns_at_least_one():
    """Pull only a couple of videos to keep the test fast."""
    vids = channel_videos(SAMPLE_CHANNEL, max_videos=3)
    assert isinstance(vids, list)
    assert len(vids) > 0
    # Schema check on first entry.
    v = vids[0]
    assert v["id"]
    assert v["kind"] in {"short", "long", "live"}


# ---------------------------------------------------------------------------
# engagement_batch
# ---------------------------------------------------------------------------


def test_engagement_batch_tolerates_bad_urls():
    out = engagement_batch([
        SAMPLE_VIDEO,
        "https://www.youtube.com/watch?v=this_should_not_exist_xyz123",
    ])
    assert len(out) == 2
    # First entry is normalised meta; second is an error stub.
    assert out[0].get("title")
    assert "_error" in out[1]


# ---------------------------------------------------------------------------
# ensure_recent_ytdlp
# ---------------------------------------------------------------------------


def test_ensure_recent_ytdlp_returns_a_version_string():
    v = ensure_recent_ytdlp()
    assert isinstance(v, str)
    assert v  # not empty
