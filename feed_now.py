#!/usr/bin/env python3

# Copyright (c) 2026 Gordon Schoenfeld
# Licensed under the MIT License.
# See LICENSE file in the project root for full license information.

import json
import sys
import os

# --- MAGIC IMPORT ---
# Importing this applies the patch to sfk_tokens() function.
import renew_tokens

# --- INITIALIZATION ---
# 1. Update tokens on disk (handles all auth logic)
client = renew_tokens.refresh_disk_tokens()

# 2. Load feeder names (static data)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INFO_FILE = os.path.join(SCRIPT_DIR, "config/feeders_config.json")

try:
    with open(INFO_FILE, "r") as f:
        feeders_list = json.load(f)
except FileNotFoundError:
    print(f"Error: {INFO_FILE} not found.")
    sys.exit(1)

# --- MAIN LOGIC ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 feed_now.py <feeder_number> <amount>")
        sys.exit(1)

    try:
        # Parse Args
        feeder_number_input = sys.argv[1]  # e.g., "1"
        feed_units = int(sys.argv[2])     # e.g., 1

        # Resolve Feeder
        feeder_data = feeders_list.get(feeder_number_input)
        if not feeder_data:
            print(
                f"Error: Feeder number '{feeder_number_input}' not found in info file.")
            sys.exit(1)

        feeder_id = feeder_data["id"]
        feeder_name = feeder_data["name"]

        # Display Amount
        cups_per_unit = {1: "1/8 cup", 2: "1/4 cup", 3: "3/8 cup", 4: "1/2 cup",
                         5: "5/8 cup", 6: "3/4 cup", 7: "7/8 cup", 8: "1 cup"}
        feed_amount_str = cups_per_unit.get(feed_units, f"{feed_units} units")

        # Find the actual feeder object from the API list
        # We match based on the ID from our local JSON
        target_feeder = next(
            (f for f in client.feeders if f.id == feeder_id), None)

        if not target_feeder:
            print(
                f"Error: Feeder '{feeder_name}' (ID: {feeder_id}) not found in API response.")
            sys.exit(1)

        # Execute
        target_feeder.feed(amount=feed_units, slow_feed=False)

    except ValueError:
        print("Error: Amount must be an integer.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
