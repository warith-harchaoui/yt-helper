# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import setup

long_description = (Path(__file__).parent / 'README.md').read_text(encoding='utf-8')

packages = \
['yt_helper']

package_data = \
{'': ['*']}

install_requires = \
['audio-helper @ git+https://github.com/warith-harchaoui/audio-helper.git@v1.1.0',
 'ffmpeg-python>=0.2.0,<0.3.0',
 'os-helper @ git+https://github.com/warith-harchaoui/os-helper.git@v1.0.0',
 'video-helper @ git+https://github.com/warith-harchaoui/video-helper.git@v1.0.0',
 'yt-dlp>=2024.12.23,<2025.0.0']

setup_kwargs = {
    'name': 'yt-helper',
    'version': '0.2.1',
    'description': 'YT Helper is a Python library that provides utility functions for downloading videos, audio, and thumbnails from platforms like YouTube, Vimeo, and DailyMotion using yt-dlp. It also supports post-processing tasks such as converting or merging media files with ffmpeg.',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'author': 'Warith Harchaoui',
    'author_email': 'warith.harchaoui@gmail.com>, Mohamed Chelali <mohamed.t.chelali@gmail.com>, Bachir Zerroug <bzerroug@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<3.14',
}


setup(**setup_kwargs)

