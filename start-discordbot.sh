#!/bin/bash

# Current working directory
cd "${0%/*}"
. venv/bin/activate

python discord_fee_base.py
