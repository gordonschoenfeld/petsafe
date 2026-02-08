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

# Unique tag to identify this specific job for deletion later
# Format: #START_FEEDER_2_AT_0830_ON_0501
JOB_TAG="#START_FEEDER_${FEEDER_NUM}_AT_$(printf "%02d%02d" $TARGET_HOUR_INT $TARGET_MIN_INT)_ON_$(printf "%02d%02d" $START_MONTH_INT $START_DAY_INT)"

# --- CHECK FOR COMMANDS ---
if ! command -v crontab &> /dev/null; then
    echo "Error: 'crontab' command not found."
    exit 1
fi

# --- CONSTRUCT THE COMMANDS ---

# 1. The actual work: Call add_scheduled_feed.sh script
DO_WORK="/bin/bash ./add_scheduled_feed.sh $TARGET_HOUR_INT:$TARGET_MIN_INT $FEEDER_NUM $AMOUNT"

# 2. The Self-Destruct: Remove any line containing this unique JOB_TAG from crontab
SELF_DESTRUCT="crontab -l | grep -v '$JOB_TAG' | crontab -"

# 3. Combine them: Do work, then immediately delete self
FULL_CMD="{ $DO_WORK; $SELF_DESTRUCT; }"

# --- SCHEDULE THE JOB ---
# Cron format: Min Hour Day Month Weekday
CRON_SCHEDULE="0 0 $START_DAY_INT $START_MONTH_INT *"

# Combine schedule, command, and the comment tag
NEW_JOB="$CRON_SCHEDULE $FULL_CMD $JOB_TAG"

# --- WRITE TO CRONTAB ---
if (crontab -l 2>/dev/null | grep -v "$JOB_TAG"; echo "$NEW_JOB") | crontab -; then
    : 
else
    echo "❌ Error: Failed to update crontab."
    exit 1
fi