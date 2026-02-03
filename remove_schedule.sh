#!/bin/bash

# Check if both arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <feeder_id> <time>"
    echo "Example: $0 12345 '30 08 * * *'"
    exit 1
fi

FEEDER_ID=$1
TIME_VAL=$2

# Specifically target the feed_now.py script
# This pattern ensures we only match the correct script, ID, and time
SEARCH_PATTERN="feed_now.py.*${FEEDER_ID}.*${TIME_VAL}"

# Check if the specific feed_now.py job exists
if ! crontab -l | grep -q "$SEARCH_PATTERN"; then
    echo "Error: No 'feed_now.py' cron job found for Feeder ID ${FEEDER_ID} with time '${TIME_VAL}'."
    exit 1
fi

# Remove only the matching feed_now.py line
(crontab -l | grep -v "$SEARCH_PATTERN") | crontab -

echo "Success: 'feed_now.py' schedule for Feeder ${FEEDER_ID} at ${TIME_VAL} has been removed."