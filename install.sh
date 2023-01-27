#!/bin/bash

python3.10 -m venv venv

# rem Upgrade pip
. venv/bin/activate

python -m pip install --upgrade pip

# rem Install requirements
python -m pip install -r requirements.txt