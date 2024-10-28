#!/bin/zsh


# This is an attempt to automate the process of setting up a new Python project using Poetry.
# DO NOT RUN IT LIKE A SCRIPT, copy and paste the commands one by one in your terminal.

# Enable debug and error checking
set -x  # Print each command before executing it
set -e  # Exit the script immediately on any command failure

# Configurations
PROJECT_NAME="yt-helper"

# Check if pytorch is okay with your python version (Getting Started section of pytorch.org)
PYTHON_VERSION="3.12"
ENV="env4yth"

DEPENDENCIES="yt-dlp ffmpeg-python git+https://github.com/warith-harchaoui/os-helper.git@main git+https://github.com/warith-harchaoui/audio-helper.git@main git+https://github.com/warith-harchaoui/video-helper.git@main"
DESCRIPTION="YT Helper is a Python library that provides utility functions for downloading videos, audio, and thumbnails from platforms like YouTube, Vimeo, and DailyMotion using yt-dlp. It also supports post-processing tasks such as converting or merging media files with ffmpeg."
AUTHORS="Warith Harchaoui <warith.harchaoui@gmail.com>, Mohamed Chelali <mohamed.t.chelali@gmail.com>, Bachir Zerroug <bzerroug@gmail.com>"

conda init
source ~/.zshrc

# Conda environment setup (optional, use only if Conda is required for some reason)
if conda info --envs | grep -q "^$ENV"; then
    echo "Environment $ENV already exists, removing it..."
    conda deactivate
    conda deactivate
    conda remove --name $ENV --all -y
fi


echo "Creating environment $ENV..."
conda create -y -n $ENV python=$PYTHON_VERSION
conda activate $ENV
conda install -y pip

rm -f pyproject.toml poetry.lock

poetry init --name $PROJECT_NAME --description "$DESCRIPTION" --author "$AUTHORS" --python "^$PYTHON_VERSION" -n

DEP_ARRAY=(${=DEPENDENCIES})
for dep in "${DEP_ARRAY[@]}"; do
    echo "Adding $dep..."
    poetry add "$dep"
done



# python requirements_to_toml.py \
#     --project_name "$PROJECT_NAME" \
#     --description "$DESCRIPTION" \
#     --authors "$AUTHORS" \
#     --python_version "^$PYTHON_VERSION" \
#     --requirements_file "requirements.txt" \
#     --output_file "pyproject.toml" \
#     --opensource

# # Poetry setup
pip install --upgrade poetry poetry2setup

poetry install

# # Generate setup.py and export requirements.txt
poetry2setup > setup.py
poetry export -f requirements.txt --output requirements.txt --without-hashes

# pip freeze > requirements.txt

# # replace git commit hash with @main
sed -i '' 's/@[a-f0-9]\{7,40\}/@main/g' requirements.txt

# Create environment.yml for conda users (optional)
cat <<EOL > environment.yml
name: $ENV
channels:
  - defaults
dependencies:
  - python=$PYTHON_VERSION
  - pip
  - pip:
      - -r file:requirements.txt
EOL

echo "Project setup completed successfully!"