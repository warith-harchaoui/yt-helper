# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import setup

long_description = (Path(__file__).parent / 'README.md').read_text(encoding='utf-8')

packages = \
['yt_helper']

package_data = \
{'': ['*']}

install_requires = \
['audio-helper @ git+https://github.com/warith-harchaoui/audio-helper.git@v1.4.1',
 'ffmpeg-python>=0.2.0,<0.3.0',
 'os-helper @ git+https://github.com/warith-harchaoui/os-helper.git@v1.3.0',
 'video-helper @ git+https://github.com/warith-harchaoui/video-helper.git@v1.4.1',
 'yt-dlp>=2024.12.23']

setup_kwargs = {
    'name': 'yt-helper',
    'version': '1.1.0',
    'description': 'YT Helper — yt-dlp wrapper for downloading videos / audio / thumbnails, resolving direct media URLs, browsing video stream catalogs, and pulling no-API engagement metadata (channel / video / comments / subtitles) for personal-branding workflows on YouTube, Vimeo, DailyMotion, Twitch VOD, and anywhere yt-dlp supports.',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'author': 'Warith HARCHAOUI',
    'author_email': 'Warith HARCHAOUI <warithmetics@deraison.ai>',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<3.14',
}


setup(**setup_kwargs)

