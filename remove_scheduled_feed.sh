#!/bin/bash

# Check if both arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <feeder_id> <time>"
    echo "Example: $0 1 10:00"
    exit 1
fi

FEEDER_ID=$1
TIME_VAL=$2

# 1. Parse HH:MM into Hour and Minute
IFS=':' read -r HOUR MINUTE <<< "$TIME_VAL"

# 2. Convert to Integers (removes leading zeros, e.g., 08 -> 8)
# We use 10# to force base-10 so bash doesn't think "08" is octal
H=$((10#$HOUR))
M=$((10#$MINUTE))

# 3. Construct the Regex Pattern
# Format: ^Minute Hour * * * ... feed_now.py FeederID
# We accept any amount argument that follows the FeederID
SEARCH_PATTERN="^${M} ${H} \* \* \* .*feed_now.py ${FEEDER_ID} "

# 4. Check if the job exists
if ! crontab -l 2>/dev/null | grep -q "$SEARCH_PATTERN"; then
    echo "Error: No schedule found for Feeder ${FEEDER_ID} at ${H}:${M}."
    echo "Debug: Searched for pattern: '$SEARCH_PATTERN'"
    exit 1
fi

# 5. Remove the job
# grep -v keeps everything that does NOT match the pattern
(crontab -l 2>/dev/null | grep -v "$SEARCH_PATTERN") | crontab -

echo "Removed schedule for Feeder ${FEEDER_ID} at ${TIME_VAL}."