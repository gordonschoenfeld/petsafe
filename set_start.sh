#!/bin/bash

# --- ARGUMENT PARSING ---
if [ "$#" -ne 6 ]; then
    echo "Usage: $0 <start_month> <start_day> <target_hour> <target_min> <feeder_num> <amount>"
    echo "Example: $0 05 01 08 30 2 4"
    echo "  (On May 1st, create the job scheduled for 08:30, Feeder 2, Amount 4)"
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

# 1. The Feeding Pattern to start (Regex)
# Logic: Anchored to start of line (^)
# Matches: Minute -> Space -> Hour -> Space -> (Wildcards) -> feed_now.py -> ID -> Amount
# Note: [ \t]+ matches both tabs and spaces.
FEED_PATTERN="^$TARGET_MIN_INT[ \t]+$TARGET_HOUR_INT[ \t]+.*feed_now.py $FEEDER_NUM $AMOUNT"

# 2. The Start Tag
# Updated to include TIME in the tag name. 
# This prevents conflicts if you schedule different starts for 8:00 vs 18:00 on the same day.
START_TAG="# START_AUTO_ADD_F${FEEDER_NUM}_A${AMOUNT}_T${TAG_TIME}"

# --- CHECK FOR EXISTING START ---
if crontab -l 2>/dev/null | grep -Fq "$START_TAG"; then
    echo "⚠️  An start job for this specific time/feeder/amount is already scheduled."
    echo "   Tag: $START_TAG"
    exit 1
fi

# --- CONSTRUCT THE 'START' COMMAND ---
# 1. Read crontab
# 2. Grep -v -E (Remove Extended Regex) -> Removes the specific feeding time
# 3. Grep -v -F (Remove Fixed String)   -> Removes this specific expiry job
# 4. Write back to crontab
# Bug fix: The random number is generated NOW and hardcoded into the job, to avoid collisions
# We use Python to sleep for a random float between 0 and 20 seconds.
# This prevents race conditions by spreading execution across millions of possible start times.
RANDOM_SLEEP="import time,random; time.sleep(random.random() * 20)"
START_CMD="/usr/local/bin/python3 -c '$RANDOM_SLEEP' && crontab -l | grep -E -v '$FEED_PATTERN' | grep -F -v '$START_TAG' | crontab -"

# --- SCHEDULE THE JOB ---
# Cron format: 00 00 Day Month * Command
CRON_SCHEDULE="00 00 $START_DAY $START_MONTH *"

# Combine into the final line
NEW_JOB="$CRON_SCHEDULE $START_CMD $START_TAG"

# Write to Crontab
if (crontab -l 2>/dev/null; echo "$NEW_JOB") | crontab -; then
    :
    # Commenting out success messages. Above colon is needed to "do nothing"
    # echo "✅ Success! Scheduled start."
    # echo "   Start Date: $START_MONTH/$START_DAY at 00:00"
    # echo "   Time:       $TARGET_HOUR:$TARGET_MIN"
    # echo "   Feeder:     $FEEDER_NUM"
    # echo "   Amount:     $AMOUNT unit(s)"
else
    echo "❌ Error: Failed to update crontab."
    exit 1
fi