#!/bin/bash

python3.10 -m venv venv

# rem Upgrade pip
. venv/bin/activate

python -m pip install --upgrade pip

# rem Install requirements
python -m pip install -r requirements.txt

# Make sure nobody accidentally commits their discord key
git update-index --assume-unchanged .env
git update-index --assume-unchanged logs/feh_coop.log