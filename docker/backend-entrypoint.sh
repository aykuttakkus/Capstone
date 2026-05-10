#!/bin/sh
set -eu

mkdir -p /app/data/store /app/data/raw /app/data/processed /app/logs
chown -R appuser:appuser /app/data/store /app/logs

exec gosu appuser "$@"
