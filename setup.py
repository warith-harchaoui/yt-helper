from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()
    
setup(
    name="yt-helper",
    version="1.0.0",
    description=(
        "YT Helper provides utility functions for downloading videos, audio, "
        "and thumbnails from YouTube, Vimeo, DailyMotion using yt-dlp, with post-processing "
        "features such as converting or merging media files using ffmpeg."
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/warith-harchaoui/yt-helper",
    author="Warith Harchaoui, Mohamed Chelali, Bachir Zerroug",
    author_email="warith.harchaoui@gmail.com", 
    license="BSD 2-Clause",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    keywords="yt-dlp youtube video downloader audio ffmpeg",
    packages=find_packages(),
    install_requires=[
        "yt-dlp",
        "Pillow",
        "ffmpeg-python",
        "os-helper",
        "audio-helper",
        "video-helper",
    ],
    python_requires=">=3.9",
)
