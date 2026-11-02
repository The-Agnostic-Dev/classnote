#!/bin/sh
set -e
python manage.py migrate --noinput
# Demo deployment: reload the sample school on every start so dates stay relative to today.
if [ "${CLASSNOTE_SEED_DEMO:-1}" = "1" ]; then
  python manage.py seed_demo
fi
exec "$@"
