#!/bin/bash
set -e
uwsgi --ini /app/sites/sandbox/deploy/uwsgi.ini
