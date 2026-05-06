#!/bin/bash
python3 -m venv .venv
source .venv/bin/activate

pip install --no-cache-dir -r app/permalink/requirements.txt

# pyright --verbose
