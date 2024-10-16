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
    verbosity = osh.verbosity()
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
    osh.check(osh.is_working_url(url), msg=f"Invalid URL:\n\t{url}")

    res = {}
    meta = _aux_ytdlp_meta_data(url)
    osh.check(meta is not None, msg=f"yt-dlp is not working on that url:\n{url}")

    res.update(meta)
    title = meta.get("title")
    res["title"] = title
    description = meta.get("description")
    res["description"] = description

    t = description.split("\n")
    t = "\n".join(t[:3])

    osh.info(f"Title:\n\t{title}")
    osh.info(f"Description (beginning):\n\t{t}")

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
        osh.info("Video url is empty")
        return False
    
    if not(osh.is_working_url(url)):
        osh.info(f"Video URL is invalid (URL not working):\n\t{url}")
        return False

    meta = _aux_ytdlp_meta_data(url)
    if meta:
        osh.info(f"yt-dlp metadata extraction is successful for {url}")
        return True

    osh.info(f"yt-dlp metadata extraction failed for {url}")
    return False


def download_thumbnail(url: str, output_path: str) -> None:
    """
    Download the thumbnail of a video from a given URL and save it to the specified output path.

    Parameters
    ----------
    url : str
        The URL of the video from which to download the thumbnail.
    output_path : str
        The path where the downloaded thumbnail should be saved.

    Returns
    -------
    None

    Notes
    -----
    This function uses yt-dlp to download the thumbnail of the specified video. It handles
    different output formats and ensures the thumbnail is saved in the desired format using PIL.
    """
    osh.info(f"Downloading thumbnail of video:\n\t{url} to:\n\t{output_path}")

    # Extract folder, basename, and thumbnail format from the output path
    folder, basename, thumb_format = osh.folder_name_ext(
        osh.relative2absolute_path(output_path)
    )
    osh.make_directory(folder)

    # Download the thumbnail to a temporary folder
    with osh.temp_folder() as temp_directory:
        o = osh.os_path_constructor([temp_directory, basename])

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
        osh.check(len(thumb_file) > 0, msg=f"Failed to download thumbnail of video {url}")
        thumb_file = osh.relative2absolute_path(thumb_file[0])

        # Check if the thumbnail needs to be converted to the desired format
        _, _, ext = osh.folder_name_ext(thumb_file)
        if ext.lower() != thumb_format.lower():
            # Read the image with PIL and save it in the desired format
            try:
                img = Image.open(thumb_file)
                img.save(output_path)
            except Exception as e:
                osh.error(f"Failed to save thumbnail to {output_path} for {url}: {e}")
        else:
            # Move the thumbnail file to the desired output path
            osh.copyfile(thumb_file, output_path)

    osh.checkfile(output_path, msg=f"Failed to download thumbnail to {output_path} from {url}")
    osh.info(f"Successful download thumbnail to {output_path} from {url}")


def download_audio(url: str, output_path: str, target_sample_rate: int = 44100) -> None:
    """
    Download the best quality audio from a given URL and save it to the specified output path.

    Parameters
    ----------
    url : str
        The URL of the video to download the audio from.
    output_path : str
        The path where the downloaded audio should be saved.
    target_sample_rate : int, optional
        The sample rate of the output audio file. Defaults to 44100.

    Returns
    -------
    None

    Notes
    -----
    This function uses yt-dlp to download the best quality audio from the given URL. It handles
    different output formats and ensures the audio is saved with the desired sample rate using a
    conversion step if necessary.
    """
    osh.info(f"Downloading audio from:\n\t{url} to:\n\t{output_path}")
    osh.check(osh.is_working_url(url), msg=f"Invalid video URL:\n\t{url}")

    # Extract folder, basename, and format from the output path
    folder, basename, audio_format = osh.folder_name_ext(osh.relative2absolute_path(output_path))
    osh.make_directory(folder)

    with osh.temp_folder() as temp_directory:
        o = osh.os_path_constructor([temp_directory, basename])

        # Set yt-dlp options to download the best quality audio
        opts = default_ytdlp_options(audio=True)
        opts["outtmpl"] = f"{o}.%(ext)s"

        # Download the audio using yt-dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Find the downloaded audio file
        received_file = glob.glob(f"{o}.*")
        osh.check(len(received_file) > 0, msg=f"Failed to download audio from {url}")
        received_file = osh.relative2absolute_path(received_file[0])
        osh.check(ah.is_valid_audio_file(received_file), msg=f"Invalid audio file: {received_file}")

        # Convert to the desired format if necessary
        _, _, ext = osh.folder_name_ext(received_file)
        if ext.lower() != audio_format.lower():
            ah.sound_converter(received_file, output_path, freq=target_sample_rate)
        else:
            osh.copyfile(received_file, output_path)

    osh.check(ah.is_valid_audio_file(output_path), msg=f"Failed to save audio to {output_path} for {url}")
    osh.info(f"Audio saved to {output_path}")

def download_video(url: str, output_path: str) -> None:
    """
    Download video from a given URL and save it to the specified output path.

    Parameters
    ----------
    url : str
        The URL of the video to be downloaded.
    output_path : str
        The path where the downloaded video should be saved.

    Returns
    -------
    None

    Notes
    -----
    This function downloads the best quality video from the given URL using yt-dlp. It handles
    different formats and ensures that the video is saved in the desired format using ffmpeg
    if necessary. The function checks whether the downloaded video is valid and converts
    it to the specified output format if needed.
    """
    osh.info(f"Downloading video from:\n\t{url} to:\n\t{output_path}")

    osh.check(osh.is_working_url(url), msg=f"Invalid video URL:\n\t{url}")

    # Extract folder, basename, and video format from the output path
    folder, basename, video_format = osh.folder_name_ext(
        osh.relative2absolute_path(output_path)
    )
    osh.make_directory(folder)

    with osh.temp_folder() as temp_directory:
        o = osh.os_path_constructor([temp_directory, basename])

        # Set yt-dlp options to download the best quality video
        opts = default_ytdlp_options(video=True)
        opts["outtmpl"] = f"{o}.%(ext)s"

        # Download the best quality video using yt-dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Find the downloaded video file
        received_file = glob.glob(f"{o}.*")
        osh.check(
            len(received_file) > 0,
            msg=f"Failed to download video from {url}",
        )
        received_file = received_file[0]
        received_file = osh.relative2absolute_path(received_file)

        # Validate the downloaded video file
        osh.check(
            vh.is_valid_video_file(received_file),
            msg=f"Invalid video file downloaded from {url}",
        )

        # Extract the extension of the downloaded file
        _, _, ext = osh.folder_name_ext(received_file)

        # If the video format differs, convert the video to the desired format
        if ext.lower() != video_format.lower():
            vh.video_converter(received_file, output_path)
        else:
            osh.movefile(received_file, output_path)

    # Validate that the video was saved successfully
    osh.checkfile(
        output_path,
        msg=f"Failed to save video to {output_path} from {url}",
    )

    osh.info(f"Successfully downloaded video from {url} to {output_path}")


def download_bad_video_with_good_sound(
    url: str, output_path: str, provided_audio_file: str = None
) -> None:
    """
    Download the worst quality video and the best quality audio from a given URL,
    and combine them into a single output file.

    Parameters
    ----------
    url : str
        The URL of the video to be downloaded.
    output_path : str
        The path where the combined video with good sound should be saved.
    provided_audio_file : str, optional
        The path to an existing audio file to be used. If not provided, the audio will be downloaded.

    Returns
    -------
    None

    Notes
    -----
    This function downloads the worst quality video and the best quality audio from
    the given URL using yt-dlp. It then combines them into a single output file with
    the desired audio and video using ffmpeg. The function handles audio format conversions
    if needed and ensures the final file is saved with valid audio and video.
    """
    osh.info(f"Downloading (bad image, good sound) video from:\n\t{url} to:\n\t{output_path}")
    
    # Extract folder, basename, and format from the output path
    folder, basename, video_format = osh.folder_name_ext(
        osh.relative2absolute_path(output_path)
    )
    osh.make_directory(folder)

    # Use a temporary folder for intermediate files
    with osh.temp_folder() as temp_directory:
        # Handle the audio file: download if not provided, or validate if provided
        if osh.emptystring(provided_audio_file):
            mp3 = osh.os_path_constructor([temp_directory, "audio.mp3"])
            download_audio(url, mp3)
            provided_audio_file = mp3
        else:
            # Check if the provided audio file is valid
            osh.check(
                ah.is_valid_audio_file(provided_audio_file),
                msg=f"Invalid audio file {provided_audio_file}",
            )
            # If the audio is not in mp3 format, convert it to mp3
            _, _, ext = osh.folder_name_ext(provided_audio_file)
            if ext.lower() != "mp3":
                mp3 = osh.os_path_constructor([temp_directory, "audio.mp3"])
                ah.sound_converter(provided_audio_file, mp3)
            else:
                mp3 = provided_audio_file
            provided_audio_file = mp3

        # Download the worst quality video
        v = osh.os_path_constructor([temp_directory, "video.mp4"])
        download_video(url, v)

        # Convert the video to low quality without sound
        bad_video_without_sound = osh.os_path_constructor([temp_directory, "video_no_sound.mp4"])
        vh.video_converter(v, bad_video_without_sound, without_sound=True, height=240)

        quiet = osh.verbosity() <= 0

        # Combine the worst video and best audio using ffmpeg
        i_video = ffmpeg.input(bad_video_without_sound)
        i_audio = ffmpeg.input(provided_audio_file)

        # Output the combined video and audio to the desired output path
        ffmpeg.output(
            i_video, i_audio, output_path, codec="copy", acodec="aac", strict="experimental"
        ).run(overwrite_output=True, quiet=quiet)

    # Validate the final combined video file
    osh.check(
        vh.is_valid_video_file(output_path),
        msg=f"Failed to save video (bad image, good sound) to {output_path} from {url}",
    )
    
    osh.info(f"Successfully downloaded video (bad image, good sound) from {url} to {output_path}")
