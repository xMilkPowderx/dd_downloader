#!/usr/bin/env bash
rm ~/django/dd_scanner/db.sqlite3
rm ~/django/dd_scanner/dd_downloader/migrations/000*
python3 ~/django/dd_scanner/manage.py makemigrations dd_downloader
python3 ~/django/dd_scanner/manage.py migrate
