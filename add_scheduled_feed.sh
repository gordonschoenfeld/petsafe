#!/bin/bash

# --- CONFIGURATION ---
# Get the absolute path of the directory where THIS script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Define the Python script location relative to this script
PYTHON_SCRIPT="$SCRIPT_DIR/feed_now.py"
# We assume 'python3' is in the path, but using full path is safer
PYTHON_EXEC="/usr/local/bin/python3"
# Log file location (Matches what we used in manual debugging)
LOG_FILE="/tmp/pet_cron.log"
# ---------------------

# 1. Input Validation
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <target_hour> <target_min> <feeder_num> <amount>"
    echo "Example: $0 14 30 2 4"
    exit 1
fi

HOUR=$1
MINUTE=$2
FEEDER_NUM=$3
AMOUNT=$4

# Validate time (Force decimal interpretation with 10# to handle leading zeros)
if ! [[ "$HOUR" =~ ^[0-9]+$ ]] || ! [[ "$MINUTE" =~ ^[0-9]+$ ]] || \
   [ "$((10#$HOUR))" -lt 0 ] || [ "$((10#$HOUR))" -gt 23 ] || \
   [ "$((10#$MINUTE))" -lt 0 ] || [ "$((10#$MINUTE))" -gt 59 ]; then
    echo "Error: Invalid time format. Please use HH:MM (00:00 to 23:59)."
    exit 1
fi

# 3. Construct the Cron Command
# Extract the directory so we can 'cd' into it
PROJECT_DIR=$(dirname "$PYTHON_SCRIPT")
SCRIPT_NAME=$(basename "$PYTHON_SCRIPT")

# We construct the command to:
# 1. Change Directory (cd) -> 2. Run Python -> 3. Log Output
FULL_COMMAND="cd $PROJECT_DIR && $PYTHON_EXEC $SCRIPT_NAME $FEEDER_NUM $AMOUNT >> $LOG_FILE 2>&1"

# 2. Build comment
CLEAN_HOUR=$((10#$HOUR))
CLEAN_MIN=$((10#$MINUTE))

TIME_STR=$(printf "%02d%02d" "$CLEAN_HOUR" "$CLEAN_MIN")

COMMENT="#FEED_F${FEEDER_NUM}_A${AMOUNT}_at_$TIME_STR"

# 3. Construct the Schedule
# Minute Hour DayOfMonth Month DayOfWeek
CRON_SCHEDULE="$((10#$MINUTE)) $((10#$HOUR)) * * *"
NEW_JOB="$CRON_SCHEDULE $FULL_COMMAND $COMMENT"

# 4. Add the job idempotently
# Checks if a job with this exact command AND arguments already exists
if crontab -l 2>/dev/null | grep -Fq "$NEW_JOB"; then
    echo "A job for Feeder $FEEDER_NUM with Amount $AMOUNT at $HOUR:$MINUTE already exists."
    echo "Skipping to prevent duplicates."
else
    (crontab -l 2>/dev/null; echo "$NEW_JOB") | crontab -
    echo "Success! Cron job created:"
    echo "   Time:   $HOUR:$MINUTE daily"
    echo "   Feeder: $FEEDER_NUM"
    echo "   Amount: $AMOUNT unit(s)"
    echo "   Log:    $LOG_FILE"
fi