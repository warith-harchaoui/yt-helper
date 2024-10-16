# Test imports
import pytest
import os_helper as osh
import video_helper as vh
import audio_helper as ah
import numpy as np
from yt_helper import (
    video_url_meta_data,
    is_valid_video_url,
    download_thumbnail,
    download_audio,
    download_video,
    download_bad_video_with_good_sound,
)

# Sample YouTube video for testing
youtube_url = "https://www.youtube.com/watch?v=YE7VzlLtp-4"
video_filename = "big-buck-bunny.mp4"
audio_filename = "big-buck-bunny.mp3"
thumbnail_filename = "thumbnail.jpg"

osh.verbosity(0)

# Helper function to get the test folder for media (video, audio, thumbnail)
def get_test_folder(filename: str) -> str:
    folder = "yt_tests"
    media_file = osh.os_path_constructor([folder, filename])
    if not osh.file_exists(media_file):
        osh.make_directory(folder)
    return media_file

# Test for video download
def test_video():
    video_file = get_test_folder(video_filename)

    assert is_valid_video_url(youtube_url), "YouTube URL should be valid"

    download_video(youtube_url, video_file)

    assert vh.is_valid_video_file(video_file), "Downloaded file should be a valid video file"
    
    video_dim = vh.video_dimensions(video_file)
    assert video_dim["width"] > 0, "Video width should be positive"
    assert video_dim["height"] > 0, "Video height should be positive"
    assert video_dim["duration"] > 0, "Video duration should be positive"
    assert video_dim["frame_rate"] > 0, "Video frame rate should be positive"
    assert video_dim["has_sound"], "Video should have sound"

# Test for audio download
def test_audio():
    audio_file = get_test_folder(audio_filename)
    download_audio(youtube_url, audio_file)

    assert ah.is_valid_audio_file(audio_file), "Downloaded file should be a valid audio file"
    
    audio_duration = ah.get_audio_duration(audio_file)
    assert audio_duration > 0, "Audio duration should be positive"

# Test for downloading a thumbnail
def test_thumbnail():
    thumbnail_file = get_test_folder(thumbnail_filename)
    download_thumbnail(youtube_url, thumbnail_file)

    assert osh.file_exists(thumbnail_file), "Thumbnail file should exist"
    
    # Optionally, test that the thumbnail can be opened
    from PIL import Image
    img = Image.open(thumbnail_file)
    assert img.size[0] > 0 and img.size[1] > 0, "Thumbnail dimensions should be valid"

# Test for video URL metadata extraction
def test_video_url_meta_data():
    metadata = video_url_meta_data(youtube_url)

    assert "title" in metadata, "Metadata should contain 'title'"
    assert "description" in metadata, "Metadata should contain 'description'"
    assert metadata["title"] != "", "Title should not be empty"
    assert metadata["description"] != "", "Description should not be empty"

# Test for downloading bad video with good sound
def test_download_bad_video_with_good_sound():
    output_video_file = get_test_folder(video_filename)
    download_bad_video_with_good_sound(youtube_url, output_video_file)

    assert vh.is_valid_video_file(output_video_file), "File should be a valid video file"
    
    video_dim = vh.video_dimensions(output_video_file)
    assert video_dim["height"] == 240, "Video should have been converted to 240p"
    assert video_dim["has_sound"], "Video should have sound"
