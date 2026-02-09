#!/bin/bash

# --- ARGUMENT PARSING ---
if [ "$#" -ne 6 ]; then
    echo "Usage: $0 <start_month> <start_day> <target_hour> <target_min> <feeder_num> <amount>"
    echo "Example: $0 05 01 08 30 2 4"
    echo "  (On May 1st (effective 00:00), set a job scheduled for 08:30, Feeder 2, Amount 4)"
    exit 1
fi

START_MONTH=$1
START_DAY=$2
TARGET_HOUR=$3
TARGET_MIN=$4
FEEDER_NUM=$5
AMOUNT=$6

# Strip leading zeros for calculation and cron-standard formatting
START_MONTH_INT=$((10#$START_MONTH))
START_DAY_INT=$((10#$START_DAY))
TARGET_HOUR_INT=$((10#$TARGET_HOUR))
TARGET_MIN_INT=$((10#$TARGET_MIN))

# --- GET ABSOLUTE PATH ---
# This finds the directory where THIS script is saved, no matter where you run it from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Unique tag to identify this specific job for deletion later
# Format: #START_F2_AT_0830_ON_0501
JOB_TAG="#START_F${FEEDER_NUM}_at_$(printf "%02d%02d" $TARGET_HOUR_INT $TARGET_MIN_INT)_ON_$(printf "%02d%02d" $START_MONTH_INT $START_DAY_INT)"

# --- CHECK FOR COMMANDS ---
if ! command -v crontab &> /dev/null; then
    echo "Error: 'crontab' command not found."
    exit 1
fi

# --- CONSTRUCT THE COMMANDS ---

# We use $SCRIPT_DIR to ensure cron finds the file.
DO_WORK="/bin/bash $SCRIPT_DIR/add_scheduled_feed.sh $TARGET_HOUR_INT $TARGET_MIN_INT $FEEDER_NUM $AMOUNT"

# The Self-Destruct
# We redirect output to /dev/null to keep cron silent on success
SELF_DESTRUCT="crontab -l | grep -v '$JOB_TAG' | crontab -"

# Combine them
FULL_CMD="{ $DO_WORK; $SELF_DESTRUCT; } >/dev/null 2>&1"

# --- SCHEDULE THE JOB ---
CRON_SCHEDULE="0 0 $START_DAY_INT $START_MONTH_INT *"

NEW_JOB="$CRON_SCHEDULE $FULL_CMD $JOB_TAG"

# --- WRITE TO CRONTAB ---
if (crontab -l 2>/dev/null | grep -v "$JOB_TAG"; echo "$NEW_JOB") | crontab -; then
    echo "✅ Success! Scheduled start for $START_MONTH/$START_DAY."
else
    echo "❌ Error: Failed to update crontab."
    exit 1
fi