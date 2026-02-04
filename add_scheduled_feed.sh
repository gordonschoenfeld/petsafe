#!/bin/bash

# --- CONFIGURATION ---
# Replace this with the absolute path to your Python script
PYTHON_SCRIPT="/Users/gordonschoenfeld/Python/PetSafe/feed_now.py"
# We assume 'python3' is in the path, but using full path is safer (e.g., /usr/bin/python3)
PYTHON_EXEC="/usr/bin/python3"
# ---------------------

# 1. Input Validation
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <HH:MM> <feeder_id> <amount>"
    echo "Example: $0 14:30 1 50"
    exit 1
fi

TIME_INPUT=$1
FEEDER_NUM=$2
AMOUNT=$3

# 2. Parse Time (HH:MM)
IFS=':' read -r HOUR MINUTE <<< "$TIME_INPUT"

# Validate time (Force decimal interpretation with 10# to handle leading zeros like 08 or 09)
if ! [[ "$HOUR" =~ ^[0-9]+$ ]] || ! [[ "$MINUTE" =~ ^[0-9]+$ ]] || \
   [ "$((10#$HOUR))" -lt 0 ] || [ "$((10#$HOUR))" -gt 23 ] || \
   [ "$((10#$MINUTE))" -lt 0 ] || [ "$((10#$MINUTE))" -gt 59 ]; then
    echo "Error: Invalid time format. Please use HH:MM (00:00 to 23:59)."
    exit 1
fi

# 3. Construct the Cron Command
# The python script receives feeder_id as arg1 and amount as arg2
FULL_COMMAND="$PYTHON_EXEC $PYTHON_SCRIPT $FEEDER_NUM $AMOUNT"

# 4. Construct the Schedule
# Minute Hour DayOfMonth Month DayOfWeek
CRON_SCHEDULE="$((10#$MINUTE)) $((10#$HOUR)) * * *"
NEW_JOB="$CRON_SCHEDULE $FULL_COMMAND"

# 5. Add the job idempotently
# Checks if a job with this exact command AND arguments already exists
if crontab -l 2>/dev/null | grep -Fq "$NEW_JOB"; then
    echo "A job for Feeder $FEEDER_NUM with Amount $AMOUNT at $HOUR:$MINUTE already exists."
    echo "Skipping to prevent duplicates."
else
    (crontab -l 2>/dev/null; echo "$NEW_JOB") | crontab -
    echo "Success! Cron job created:"
    echo "   Time: $HOUR:$MINUTE daily  |  Feeder: $FEEDER_NUM  |  Amount: $AMOUNT units"
fi