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

import yt_dlp
import glob
from PIL import Image
import ffmpeg
import os_helper as osh
import audio_helper as ah
import video_helper as vh
from typing import Union

import logging

def default_ytdlp_options(overwrites: bool = True, audio: bool = False, video: bool = False) -> dict:
    """
    Generate default yt-dlp options based on provided parameters.

    Parameters
    ----------
    overwrites : bool, optional
        Whether to overwrite existing files. Default is True.
    audio : bool, optional
        Whether to download audio only. Default is False.
    video : bool, optional
        Whether to download video only (overrides audio). Default is False.

    Returns
    -------
    dict
        A dictionary of options for yt-dlp.

    Notes
    -----
    The function sets various options for yt-dlp. If `audio` is set to True,
    the format is set to download the best audio available. If `video` is set
    to True, it overrides the audio flag and downloads video+audio.
    """
    verbosity = 0
    options = {
        "quiet": verbosity == 0,
        "no_warnings": verbosity < 2,
        "verbose": verbosity >= 2,
        "progress_hooks": [lambda d: None],
        "debug_printtraffic": verbosity == 3,
        "include_ads": False,
        "forceurl": verbosity < 2,
        "overwrites": overwrites,
    }

    cookies_files = glob.glob("*ytdlp_cookie.txt")
    osh.remove_files(cookies_files)
    now = osh.now_string(fmt= "filename")
    cookie_file = f"{now}_ytdlp_cookie.txt"

    options.update({
        "cookiefile": cookie_file,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
            "Accept-Language": "en-US,en;q=0.5",
        },
        # "proxy": "http://your.proxy.server:port", # in case we are banned
        "force_generic_extractor": True,
    })

    options["extractor_args"] = {
        "youtube": {
            "player_skip": ["js"]
        }
    }

    if audio:
        options["format"] = "bestaudio/best"

    if video:
        options["format"] = "bestvideo+bestaudio/best"

    return options


def _aux_ytdlp_meta_data(url: str) -> Union[dict, None]:
    """
    Extract metadata from a video URL using yt-dlp.

    Parameters
    ----------
    url : str
        The URL of the video.

    Returns
    -------
    dict or None
        A dictionary containing the metadata if extraction is successful, None otherwise.

    Notes
    -----
    This function is intended for internal use to extract video metadata without
    downloading the actual content.
    """
    meta = None
    try:
        opt = default_ytdlp_options()
        with yt_dlp.YoutubeDL(opt) as ydl:
            meta = ydl.extract_info(url, download=False)
    except Exception:
        pass
    return meta


def video_url_meta_data(url: str) -> dict:
    """
    Retrieve metadata from a video URL without downloading the video.

    Parameters
    ----------
    url : str
        The URL of the video.

    Returns
    -------
    dict
        A dictionary containing the video's metadata, including title and description.

    Notes
    -----
    The function checks for metadata extraction success, logs the title and
    a part of the description, and returns metadata.
    """
    assert osh.is_working_url(url), f"Invalid URL:\n\t{url}"

    res = {}
    meta = _aux_ytdlp_meta_data(url)
    assert meta is not None, f"yt-dlp is not working on that url:\n{url}"

    res.update(meta)
    title = meta.get("title")
    res["title"] = title
    description = meta.get("description")
    res["description"] = description

    t = description.split("\n")
    t = "\n".join(t[:3])

    logging.info(f"Title:\n\t{title}")
    logging.info(f"Description (beginning):\n\t{t}")

    return res


def is_valid_video_url(url: str) -> bool:
    """
    Check if a given URL is a valid video URL using yt-dlp.

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    bool
        True if the URL is valid, False otherwise.

    Notes
    -----
    This function extracts metadata from the URL using yt-dlp to determine
    if the URL points to a valid video.
    """
    if osh.emptystring(url):
        logging.info("Video url is empty")
        return False
    
    if not(osh.is_working_url(url)):
        logging.info(f"Video URL is invalid (URL not working):\n\t{url}")
        return False

    meta = _aux_ytdlp_meta_data(url)
    if meta:
        logging.info(f"yt-dlp metadata extraction is successful for {url}")
        return True

    logging.info(f"yt-dlp metadata extraction failed for {url}")
    return False


def download_thumbnail(url: str, output_path: str=None) -> str:
    """
    Download the thumbnail of a video from a given URL and save it to the specified output path.

    Parameters
    ----------
    url : str
        The URL of the video from which to download the thumbnail.
    output_path : str, optional
        The path where the downloaded thumbnail should be saved.

    Returns
    -------
    str
        Path of downloaded thumbnail

    Notes
    -----
    This function uses yt-dlp to download the thumbnail of the specified video. It handles
    different output formats and ensures the thumbnail is saved in the desired format using PIL.
    """
    if osh.emptystring(output_path):
        metadata = video_url_meta_data(url)
        title = metadata["title"]
        basename = osh.asciistring(title)
        output_path = f"{basename}.png"
        output_path = osh.relative2absolute_path(output_path)

    if osh.file_exists(output_path):
        logging.info(f"Thumbnail already exists:\n\t{output_path}")
        return output_path
    
    logging.info(f"Downloading thumbnail of video:\n\t{url} to:\n\t{output_path}")

    # Extract folder, basename, and thumbnail format from the output path
    folder, basename, thumb_format = osh.folder_name_ext(
        osh.relative2absolute_path(output_path)
    )
    osh.make_directory(folder)

    # Download the thumbnail to a temporary folder
    with osh.temporary_folder() as temp_directory:
        o = osh.join(temp_directory, basename)

        # Set yt-dlp options to download only the thumbnail
        opts = default_ytdlp_options()
        opts["skip_download"] = True
        opts["writethumbnail"] = True
        opts["outtmpl"] = f"{o}.%(ext)s"

        # Download the thumbnail using yt-dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Find the downloaded thumbnail file
        thumb_file = glob.glob(f"{o}.*")
        assert len(thumb_file) > 0, f"Failed to download thumbnail of video {url}"
        thumb_file = osh.relative2absolute_path(thumb_file[0])

        # Check if the thumbnail needs to be converted to the desired format
        _, _, ext = osh.folder_name_ext(thumb_file)
        if ext.lower() != thumb_format.lower():
            # Read the image with PIL and save it in the desired format
            try:
                img = Image.open(thumb_file)
                img.save(output_path)
            except Exception as e:
                raise f"Failed to save thumbnail to {output_path} for {url}: {e}"
        else:
            # Move the thumbnail file to the desired output path
            osh.copyfile(thumb_file, output_path)

    osh.checkfile(output_path, msg=f"Failed to download thumbnail to {output_path} from {url}")
    logging.info(f"Successful download thumbnail to {output_path} from {url}")
    
    return output_path


def download_audio(url: str, output_path: str=None, target_sample_rate: int = 44100) -> str:
    """
    Download the best quality audio from a given URL and save it to the specified output path.

    Parameters
    ----------
    url : str
        The URL of the video to download the audio from.
    output_path : str, optional
        The path where the downloaded audio should be saved.
    target_sample_rate : int, optional
        The sample rate of the output audio file. Defaults to 44100.

    Returns
    -------
    str
        Path of downloaded audio
        
    Notes
    -----
    This function uses yt-dlp to download the best quality audio from the given URL. It handles
    different output formats and ensures the audio is saved with the desired sample rate using a
    conversion step if necessary.
    """
    if osh.emptystring(output_path):
        metadata = video_url_meta_data(url)
        title = metadata["title"]
        basename = osh.asciistring(title)
        output_path = f"{basename}.mp3"
        output_path = osh.relative2absolute_path(output_path)

    if osh.file_exists(output_path) and ah.is_valid_audio_file(output_path):
        logging.info(f"Thumbnail already exists:\n\t{output_path}")
        return output_path
    
    logging.info(f"Downloading audio from:\n\t{url} to:\n\t{output_path}")
    assert osh.is_working_url(url), f"Invalid video URL:\n\t{url}"

    # Extract folder, basename, and format from the output path
    folder, basename, audio_format = osh.folder_name_ext(osh.relative2absolute_path(output_path))
    osh.make_directory(folder)

    with osh.temporary_folder() as temp_directory:
        o = osh.join(temp_directory, basename)

        # Set yt-dlp options to download the best quality audio
        opts = default_ytdlp_options(audio=True)
        opts["outtmpl"] = f"{o}.%(ext)s"

        # Download the audio using yt-dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Find the downloaded audio file
        received_file = glob.glob(f"{o}.*")
        assert len(received_file) > 0, f"Failed to download audio from {url}"
        received_file = osh.relative2absolute_path(received_file[0])
        assert ah.is_valid_audio_file(received_file), f"Invalid audio file: {received_file}"

        # Convert to the desired format if necessary
        _, _, ext = osh.folder_name_ext(received_file)
        if ext.lower() != audio_format.lower():
            ah.sound_converter(received_file, output_path, freq=target_sample_rate)
        else:
            osh.copyfile(received_file, output_path)

    assert ah.is_valid_audio_file(output_path), f"Failed to save audio to {output_path} for {url}"
    logging.info(f"Audio saved to {output_path}")

    return output_path

def download_video(url: str, output_path: str=None) -> str:
    """
    Download video from a given URL and save it to the specified output path.

    Parameters
    ----------
    url : str
        The URL of the video to be downloaded.
    output_path : str, optional
        The path where the downloaded video should be saved.

    Returns
    -------
    str
        Path of downloaded video

    Notes
    -----
    This function downloads the best quality video from the given URL using yt-dlp. It handles
    different formats and ensures that the video is saved in the desired format using ffmpeg
    if necessary. The function checks whether the downloaded video is valid and converts
    it to the specified output format if needed.
    """
    if osh.emptystring(output_path):
        metadata = video_url_meta_data(url)
        title = metadata["title"]
        basename = osh.asciistring(title)
        output_path = f"{basename}.mp4"
        output_path = osh.relative2absolute_path(output_path)

    if osh.file_exists(output_path) and vh.is_valid_video_file(output_path):
        logging.info(f"Video already exists:\n\t{output_path}")
        return output_path
    
    
    logging.info(f"Downloading video from:\n\t{url} to:\n\t{output_path}")

    assert osh.is_working_url(url), f"Invalid video URL:\n\t{url}"

    # Extract folder, basename, and video format from the output path
    folder, basename, video_format = osh.folder_name_ext(
        osh.relative2absolute_path(output_path)
    )
    osh.make_directory(folder)

    with osh.temporary_folder() as temp_directory:
        o = osh.join([temp_directory, basename])

        # Set yt-dlp options to download the best quality video
        opts = default_ytdlp_options(video=True)
        opts["outtmpl"] = f"{o}.%(ext)s"

        # Download the best quality video using yt-dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Find the downloaded video file
        received_file = glob.glob(f"{o}.*")
        assert len(received_file) > 0, f"Failed to download video from {url}"
        received_file = received_file[0]
        received_file = osh.relative2absolute_path(received_file)

        # Validate the downloaded video file
        assert vh.is_valid_video_file(received_file), f"Invalid video file downloaded from {url}"

        # Extract the extension of the downloaded file
        _, _, ext = osh.folder_name_ext(received_file)

        # If the video format differs, convert the video to the desired format
        if ext.lower() != video_format.lower():
            vh.video_converter(received_file, output_path)
        else:
            osh.copyfile(received_file, output_path)

    # Validate that the video was saved successfully
    osh.checkfile(
        output_path,
        msg=f"Failed to save video to {output_path} from {url}",
    )

    logging.info(f"Successfully downloaded video from\n\t{url} to\n\t{output_path}")

    return output_path

