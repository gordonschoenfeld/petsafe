#!/bin/bash

# --- ARGUMENT CHECK ---
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <FEEDER_NUM> <HOUR> <MINUTE>"
    echo "Example: $0 1 08 30"
    exit 1
fi

FEEDER_NUM=$1
TARGET_HOUR=$2
TARGET_MIN=$3

# --- 1. NORMALIZE INPUTS (Strip Zeros for Math) ---
# We force base-10 to prevent octal errors (e.g. 08 -> error)
HOUR_INT=$((10#$TARGET_HOUR))
MIN_INT=$((10#$TARGET_MIN))

# --- 2. BUILD ROBUST REGEX ---
# Logic: "0?X" means "match X, optionally preceded by 0"
# This successfully matches both "8" and "08"
if [ "$HOUR_INT" -lt 10 ]; then
    HOUR_REGEX="0?$HOUR_INT"
else
    HOUR_REGEX="$HOUR_INT"
fi

if [ "$MIN_INT" -lt 10 ]; then
    MIN_REGEX="0?$MIN_INT"
else
    MIN_REGEX="$MIN_INT"
fi

# The pattern we search for in crontab:
# Example: ^0?0 0?1 .*feed_now.py 1 
SEARCH_PATTERN="^$MIN_REGEX $HOUR_REGEX .*feed_now.py $FEEDER_NUM "

# --- 3. CHECK IF JOB EXISTS ---
# FIX: Added -E so grep understands that '?' is a special character
if ! crontab -l | grep -Eq "$SEARCH_PATTERN"; then
    echo "Error: No schedule found for Feeder $FEEDER_NUM at $TARGET_HOUR:$TARGET_MIN."
    # echo "Debug: Searched for regex: '$SEARCH_PATTERN'"
    exit 1
fi

# --- 4. REMOVE THE JOB ---
# FIX: Added -E so it correctly identifies the line to delete
TMP_CRON=$(mktemp)
crontab -l | grep -Ev "$SEARCH_PATTERN" > "$TMP_CRON"

# Install the new crontab
if crontab "$TMP_CRON"; then
    rm "$TMP_CRON"
    # Silent success is usually preferred for scripts, but you can uncomment below to see it:
    # echo "✅ Success! Removed schedule for Feeder $FEEDER_NUM at $TARGET_HOUR:$TARGET_MIN."
else
    rm "$TMP_CRON"
    echo "❌ Error: Failed to write new crontab."
    exit 1
fi