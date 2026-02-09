#!/bin/bash

# --- ARGUMENT PARSING ---
if [ "$#" -ne 6 ]; then
    echo "Usage: $0 <expiry_month> <expiry_day> <target_hour> <target_min> <feeder_num> <amount>"
    echo "Example: $0 05 01 08 30 2 4"
    echo "  (On May 1st (effective 23:59), delete the job scheduled for 08:30, Feeder 2, Amount 4)"
    exit 1
fi

EXPIRY_MONTH=$1
EXPIRY_DAY=$2
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

# 1. The Feeding Pattern to expiry (Regex)
# Logic: Anchored to start of line (^)
# Matches: Minute -> Space -> Hour -> Space -> (Wildcards) -> feed_now.py -> ID -> Amount
# Note: [ \t]+ matches both tabs and spaces.
FEED_PATTERN="^$TARGET_MIN_INT[ \t]+$TARGET_HOUR_INT[ \t]+.*feed_now.py $FEEDER_NUM $AMOUNT"

# 2. The Expiry Tag
# This prevents conflicts if you schedule different expiries for 8:00 vs 18:00 on the same day.
EXPIRY_TAG="#EXPIRY_AUTO_REMOVE_F${FEEDER_NUM}_A${AMOUNT}_at_T${TAG_TIME}"

# --- CHECK FOR EXISTING EXPIRY ---
if crontab -l 2>/dev/null | grep -Fq "$EXPIRY_TAG"; then
    echo "⚠️  An expiry job for this specific time/feeder/amount is already scheduled."
    echo "   Tag: $EXPIRY_TAG"
    exit 1
fi

# --- CONSTRUCT THE 'SELF-DESTRUCT' COMMAND ---
# 1. Read crontab
# 2. Grep -v -E (Kill Extended Regex) -> Kills the specific feeding time
# 3. Grep -v -F (Kill Fixed String)   -> Kills this specific expiry job
# 4. Write back to crontab
# The random number is generated NOW and hardcoded into the job, to avoid collisions
# We use Python to sleep for a random float between 0 and 20 seconds.
# This prevents race conditions by spreading execution across millions of possible start times.
RANDOM_SLEEP="import time,random; time.sleep(random.random() * 20)"
KILLER_CMD="/usr/local/bin/python3 -c '$RANDOM_SLEEP' && crontab -l | grep -E -v '$FEED_PATTERN' | grep -F -v '$EXPIRY_TAG' | crontab -"

# --- SCHEDULE THE JOB ---
# Cron format: 59 23 Day Month * Command
CRON_SCHEDULE="59 23 $EXPIRY_DAY $EXPIRY_MONTH *"

# Combine into the final line
NEW_JOB="$CRON_SCHEDULE $KILLER_CMD $EXPIRY_TAG"

# Write to Crontab
if (crontab -l 2>/dev/null; echo "$NEW_JOB") | crontab -; then
    :
    # Commenting out success messages. Above colon is needed to "do nothing"
    # echo "✅ Success! Scheduled expiration ☠️."
    # echo "   Expiry Date: $EXPIRY_MONTH/$EXPIRY_DAY at 23:59"
    # echo "   Time:        $TARGET_HOUR:$TARGET_MIN"
    # echo "   Feeder:      $FEEDER_NUM"
    # echo "   Amount:      $AMOUNT unit(s)"
else
    echo "❌ Error: Failed to update crontab."
    exit 1
fi