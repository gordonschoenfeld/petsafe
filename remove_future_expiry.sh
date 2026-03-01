#!/bin/bash

# Copyright (c) 2026 Gordon Schoenfeld
# Licensed under the MIT License.
# See LICENSE file in the project root for full license information.

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
# Example: #EXPIRY_AUTO_REMOVE_F2_A4_at_0830
SEARCH_PATTERN="#EXPIRY_AUTO_REMOVE_F${FEEDER_NUM}_A.*_at_$(printf "%02d%02d" $HOUR_INT $MIN_INT)"


# --- 3. CHECK IF JOB EXISTS ---
if ! crontab -l | grep -Eq "$SEARCH_PATTERN"; then
    echo "⚠️ ERROR: No expiry found for Feeder $FEEDER_NUM at $TARGET_HOUR:$TARGET_MIN."
    exit 1
fi

# --- 4. REMOVE THE JOB ---
TMP_CRON=$(mktemp)
crontab -l | grep -Ev "$SEARCH_PATTERN" > "$TMP_CRON"

# Install the new crontab
if crontab "$TMP_CRON"; then
    rm "$TMP_CRON"
    # Silent success is usually preferred for scripts, but you can uncomment below to see it:
    # echo "Success! Removed schedule for Feeder $FEEDER_NUM at $TARGET_HOUR:$TARGET_MIN."
else
    rm "$TMP_CRON"
    echo "⚠️ ERROR: Failed to remove expiry command."
    exit 1
fi