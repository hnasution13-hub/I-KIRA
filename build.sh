#!/usr/bin/env bash
set -o errexit

python mnage.py migrate --noinput
pip install -r requirements.txt
pip install --upgrade pip
python manage.py collectstatic --noinput