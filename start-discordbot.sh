#!/bin/bash

# Current working directory
cd "${0%/*}"
. venv/bin/activate

python discordbot_base.py
