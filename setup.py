# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['yt_helper']

package_data = \
{'': ['*']}

install_requires = \
['audio-helper @ git+https://github.com/warith-harchaoui/audio-helper.git@main',
 'ffmpeg-python>=0.2.0,<0.3.0',
 'os-helper @ git+https://github.com/warith-harchaoui/os-helper.git@main',
 'video-helper @ git+https://github.com/warith-harchaoui/video-helper.git@main',
 'yt-dlp>=2024.10.22,<2025.0.0']

setup_kwargs = {
    'name': 'yt-helper',
    'version': '0.1.0',
    'description': 'YT Helper is a Python library that provides utility functions for downloading videos, audio, and thumbnails from platforms like YouTube, Vimeo, and DailyMotion using yt-dlp. It also supports post-processing tasks such as converting or merging media files with ffmpeg.',
    'long_description': '# YT Helper\n\n`YT Helper` belongs to a collection of libraries called `AI Helpers` developed for building Artificial Intelligence.\n\n[🕸️ AI Helpers](https://harchaoui.org/warith/ai-helpers)\n\n[![logo](logo.png)](https://harchaoui.org/warith/ai-helpers)\n\nYT Helper is a Python library that provides utility functions for downloading videos, audio, and thumbnails from platforms like YouTube, Vimeo, and DailyMotion using `yt-dlp`.\nIt also supports post-processing tasks such as converting or merging media files with `ffmpeg`.\n\n# Installation\n\n## Install Package\n\nWe recommend using Python environments. Check this link if you\'re unfamiliar with setting one up:\n\n[🥸 Tech tips](https://harchaoui.org/warith/4ml/#install)\n\n### Install `yt-dlp` and `ffmpeg`\n\nTo install YT Helper, you must install the following dependencies:\n\n- For macOS 🍎\n  \nGet [brew](https://brew.sh) and install the necessary packages:\n```bash\nbrew install yt-dlp\nbrew install ffmpeg\n```\n\n- For Ubuntu 🐧\n```bash\nsudo apt install yt-dlp\nsudo apt install ffmpeg\n```\n\n- For Windows 🪟\n  - `yt-dlp`: Download [yt-dlp from its repository](https://github.com/yt-dlp/yt-dlp) and follow the instructions for your system.\n\n  - `ffmpeg`: Go to the [FFmpeg website](https://ffmpeg.org/download.html) and follow the instructions for downloading FFmpeg. You\'ll need to manually add FFmpeg to your system PATH.\n\n## Install `YT Helper`:\n```bash\npip install --force-reinstall --no-cache-dir git+https://github.com/warith-harchaoui/yt-helper.git@main\n```\n\n# Usage\n\nHere’s an example of how to use YT Helper to download a video, extract metadata, and download the audio:\n\n```python\nimport yt_helper as yth\nimport video_helper as vh\nimport audio_helper as ah\nimport os_helper as osh\nimport os\n\nosh.verbosity(0)\n\n# Example YouTube URL\nyoutube_url = "https://www.youtube.com/watch?v=YE7VzlLtp-4"\n\nfolder = "yt_tests"\nos.makedirs(folder, exist_ok=True)\n\n# Download a video\nvideo = "big-buck-bunny.mp4"\nvideo = os.path.join(folder, video)\nyth.download_video(youtube_url, video)\n\n# Extract metadata from the video URL\nmetadata = yth.video_url_meta_data(youtube_url)\nprint(metadata["title"])\n# Big Buck Bunny\n\nprint(metadata["duration"])\n# 597\n\nprint(metadata["description"])\n# Big Buck Bunny tells the story of a giant rabbit with a heart bigger than himself. When one sunny day three rodents rudely harass him, something snaps... and the rabbit ain\'t no bunny anymore! In the typical cartoon tradition he prepares the nasty rodents a comical revenge.\n# \n# Licensed under the Creative Commons Attribution license\n# \n# http://www.bigbuckbunny.org/\n\nprint(metadata["channel"])\n# Blender\n\ndetails = vh.video_dimensions(video)\nprint(details)\n# {\'width\': 1280, \'height\': 720, \'duration\': 596.458, \'frame_rate\': 24.0, \'has_sound\': True}\n\n# Download the audio from the video\naudio = "big-buck-bunny.mp3"\naudio = os.path.join(folder, audio)\nyth.download_audio(youtube_url, audio)\n\naudio, sample_rate = ah.load_audio(audio)\nprint(sample_rate)\n# 44100\n```\n\n# Features\n- *Video Downloading*: Download videos from platforms like YouTube, Vimeo, and DailyMotion using yt-dlp.\n- *Audio Downloading*: Download the best available audio from videos.\n- *Thumbnail Downloading*: Extract and save video thumbnails.\n- *Video Metadata*: Retrieve metadata such as title, description, and duration without downloading the entire video.\n- *Flexible yt-dlp Options*: Customize download options like format and verbosity using helper functions.\n\n# Authors\n - [Warith Harchaoui](https://harchaoui.org/warith)\n - [Mohamed Chelali](https://mchelali.github.io)\n - [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug)\n',
    'author': 'Warith Harchaoui',
    'author_email': 'warith.harchaoui@gmail.com>, Mohamed Chelali <mohamed.t.chelali@gmail.com>, Bachir Zerroug <bzerroug@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.12,<4.0',
}


setup(**setup_kwargs)

