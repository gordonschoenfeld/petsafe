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

# Strip leading zeros to match crontab format (e.g., "08" -> "8")
TARGET_HOUR_INT=$((10#$TARGET_HOUR))
TARGET_MIN_INT=$((10#$TARGET_MIN))

# This ensures Python can parse it reliably as HHMM
TAG_TIME=$(printf "%02d%02d" $TARGET_HOUR_INT $TARGET_MIN_INT)

# --- CHECK FOR COMMANDS ---
if ! command -v crontab &> /dev/null; then
    echo "Error: 'crontab' command not found."
    exit 1
fi

# --- CONSTRUCT PATTERNS ---


# --- CHECK FOR EXISTING SCHEDULE ALREADY IN PLACE ---


# --- CHECK FOR EXISTING SCHEDULE PENDING ---

# --- CONSTRUCT THE 'SELF-DESTRUCT' COMMAND ---
# 1. Read crontab
# 2. Write back to crontab
# 3. Kill this command itself


# --- SCHEDULE THE JOB ---
# Cron format: 59 23 Day Month * Command
CRON_SCHEDULE="00 00 $START_DAY $START_MONTH *"

# Combine into the final line
NEW_JOB="$CRON_SCHEDULE $KILLER_CMD $START_TAG"

# Write to Crontab
if (crontab -l 2>/dev/null; echo "$NEW_JOB") | crontab -; then
    :
    # Commenting out success messages. Above colon is needed to "do nothing"
    # echo "✅ Success! Scheduled start."
    # echo "   Start Date:  $START_MONTH/$START_DAY at 23:59"
    # echo "   Time:        $TARGET_HOUR:$TARGET_MIN"
    # echo "   Feeder:      $FEEDER_NUM"
    # echo "   Amount:      $AMOUNT unit(s)"
else
    echo "❌ Error: Failed to update crontab."
    exit 1
fi