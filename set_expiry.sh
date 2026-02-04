#!/bin/bash

# --- ARGUMENT PARSING ---
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <kill_month> <kill_day> <feeder_num> <amount>"
    echo "Example: $0 05 01 2 4 (Deletes all jobs for Feeder 2, Amount 4 on May 1st)"
    exit 1
fi

KILL_MONTH=$1
KILL_DAY=$2
FEEDER_NUM=$3
AMOUNT=$4

# --- CHECK FOR 'at' COMMAND ---
if ! command -v at &> /dev/null; then
    echo "Error: 'at' command not found."
    exit 1
fi

# --- CONSTRUCT PATTERNS ---
# 1. The Feeding Pattern to kill (Regex)
# Matches: feed_now.py [space] ID [space] AMOUNT [space or end of line]
FEED_PATTERN="feed_now.py $FEEDER_NUM $AMOUNT"


# 2. The Expiry Tag (To identify THIS cleanup job so it can delete itself)
EXPIRY_TAG="# EXPIRY_AUTO_REMOVE_F${FEEDER_NUM}_A${AMOUNT}"

# --- CHECK FOR EXISTING EXPIRY ---
if crontab -l 2>/dev/null | grep -Fq "$EXPIRY_TAG"; then
    echo "⚠️  An expiry job for Feeder $FEEDER_NUM (Amount $AMOUNT) is already scheduled."
    echo "Please remove it manually if you want to change the date."
    exit 1
fi

# --- CONSTRUCT THE 'KILLER' COMMAND ---
# This complex one-liner runs at 23:59.
# Logic: 
# 1. Read crontab
# 2. Grep -v (Remove) the feeding schedule
# 3. Grep -v (Remove) the expiry tag (itself)
# 4. Write back to crontab
KILLER_CMD="crontab -l | grep -E -v '$FEED_PATTERN' | grep -F -v '$EXPIRY_TAG' | crontab -"

# --- SCHEDULE THE JOB ---
# Cron format: 59 23 Day Month * Command
CRON_SCHEDULE="59 23 $D $M *"

# Combine into the final line
NEW_JOB="$CRON_SCHEDULE $KILLER_CMD $EXPIRY_TAG"

# Write to Crontab
(crontab -l 2>/dev/null; echo "$NEW_JOB") | crontab -

echo "✅ Success! Scheduled expiration ☠️."
echo "   Date:   $KILL_MONTH/$KILL_DAY at 23:59"
echo "   Feeder: $FEEDER_NUM"
echo "   Amount: $AMOUNT unit(s)"

echo "   Action: All matching feeding jobs will be removed."