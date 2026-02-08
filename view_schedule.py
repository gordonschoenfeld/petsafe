#!/usr/bin/python3

import subprocess
import sys
import json
import os
import re
from datetime import datetime


# --- MAGIC IMPORT ---
# Importing this applies the patch to sfk_tokens() function.
import renew_tokens

# --- INITIALIZATION ---
# 1. Update tokens on disk (handles all auth logic)
client = renew_tokens.refresh_disk_tokens()

# 2. Load feeder names (static data)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INFO_FILE = os.path.join(SCRIPT_DIR, "feeders_general_info.json")

# --- MAIN LOGIC ---
try:
    with open(INFO_FILE, "r") as f:
        feeders_list = json.load(f)
except FileNotFoundError:
    print(f"Error: {INFO_FILE} not found.")
    sys.exit(1)


def fetch_feeder_info() -> dict:
    clean_data: dict = {}

    try:
        feeders = client.feeders
        if not feeders:
            print("No feeders found on this account.")
            return {}  # Return empty dict instead of None to prevent crashes

        for feeder in feeders:
            clean_data[feeder.id] = {}
            # id: ***REMOVED*** is Under ***REMOVED***
            if feeder.id == ***REMOVED***:
                num = "1"
            # id: ***REMOVED*** is ***REMOVED***
            elif feeder.id == ***REMOVED***:
                num = "2"
            else:
                num = str(feeder.id)  # Fallback if ID is unknown

            clean_data[feeder.id]["feeder_number"] = num
            # Use .get() safely in case 'thing_name' is missing
            clean_data[feeder.id]["api_id"] = feeder.data.get(
                "thing_name", "Unknown")

            # Use safe lookups for feeders_list
            if num in feeders_list:
                clean_data[feeder.id]["name"] = feeders_list[num]["name"]
                clean_data[feeder.id]["default_amount"] = feeders_list[num]["default_amount"]
            else:
                clean_data[feeder.id]["name"] = f"Feeder {num}"
                clean_data[feeder.id]["default_amount"] = 1

            # Display schedules
            clean_data[feeder.id]["schedules"] = []
            for schedule in feeder.data["schedules"]:
                clean_data[feeder.id]["schedules"].append({
                    "time": schedule["time"],       # <--- FIX: Use "time"
                    "amount": schedule["amount"],
                    "id": schedule["id"]
                })

            # Now this sort will work because "time" exists
            clean_data[feeder.id]["schedules"].sort(key=lambda x: x['time'])
            clean_data[feeder.id]["slow_feed"] = False

        return clean_data

    except Exception as e:
        print(f"\nAn error occurred in fetch_feeder_info: {e}")
        return {}  # Return empty dict on error so we don't crash later


def convert_date_to_day(date_str) -> str:
    # Takes MM/DD as input

    # 1. Get the current date (normalized to midnight for accurate comparison)
    now = datetime.now()

    # 2. Parse the "MM/DD" string using the current year temporarily
    # We append the current year to make it a valid datetime object
    dt_object = datetime.strptime(f"{date_str}/{now.year}", "%m/%d/%Y")

    # 3. Check if this date is in the past
    # (We compare .date() to ignore the specific time of day)
    if dt_object.date() < now.date():
        # If it's in the past, add 1 to the year
        dt_object = dt_object.replace(year=now.year + 1)

    # 4. Get the 3-letter weekday abbreviation based on the correct year
    day_abbr = dt_object.strftime("%a")

    return day_abbr


def view_schedule(clean_data: dict) -> list[tuple]:

    # --- FETCH CRON SCHEDULES ---
    def get_cron_lines() -> list:
        """Fetches the raw crontab output."""
        try:
            # Run 'crontab -l' and capture output
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # If no crontab exists, return empty list
                return []

            # Split into lines and remove empty ones
            return [line for line in result.stdout.splitlines() if line.strip()]

        except FileNotFoundError:
            print("Error: 'crontab' command not found.")
            sys.exit(1)

    def parse_cron_add_line(line) -> tuple | None:
        """
        Parses a single cron line to extract hour, minute, feeder, and amount.
        Assumes format: MIN HOUR * * * cd dir_path && python_path script_path FEEDER_ID AMOUNT >> logfile 2>&1
        """
        # The name of the script we are looking for in the cron list
        target_script = "feed_now.py"
        parts = line.split()

        # 1. Basic check
        if len(parts) < 6 or target_script not in line:
            return None

        # 2. Extract Time (First two standard fields)
        minute = parts[0].zfill(2)
        hour = parts[1].zfill(2)

        # 3. Extract Arguments Dynamically
        # We find the index of 'feed_now.py' and look at the neighbors (index+1, index+2)
        try:
            script_idx = parts.index(target_script)

            # Arg 1 (Feeder ID) is right after the script name
            feeder_id = parts[script_idx + 1]

            # Arg 2 (Amount) is right after Feeder ID
            amount = int(parts[script_idx + 2])

        except (ValueError, IndexError):
            # ValueError: target_script not in list (though we checked string earlier)
            # IndexError: Line ends too early (missing arguments)
            return None

        # 4. Lookup friendly name
        # Ensure this path is correct relative to where you run this viewing script!
        try:
            with open("feeders_general_info.json", "r") as f:
                feeders_list = json.load(f)
                # Assuming feeders_list is a Dict where keys are strings
                feeder_info = feeders_list.get(str(feeder_id), {})
                feeder_name = feeder_info.get("name", f"Feeder #{feeder_id}")
        except (FileNotFoundError, json.JSONDecodeError):
            feeder_name = f"Feeder #{feeder_id}"

        return feeder_name, hour, minute, amount, ""

    def parse_cron_expiry_line(line) -> tuple | None:
        log_line = line

        # Define the pattern with named groups for easy extraction
        pattern = re.compile(
            r"^59 23 (?P<day>\d+) (?P<month>\d+) \* .*? # EXPIRY_AUTO_REMOVE_F(?P<feeder>\d+)_A(?P<amount>[^_]+)_T(?P<time>\d{4})$")

        match = pattern.search(log_line)

        if match:
            data = match.groupdict()

            try:
                with open("feeders_general_info.json", "r") as f:
                    feeders_list = json.load(f)

                # Assemble output vars
                feeder_num: str = str(data['feeder'])
                # Use .get to avoid crashes if JSON is out of sync
                feeder_info = feeders_list.get(feeder_num, {})
                feeder_name: str = feeder_info.get(
                    'name', f"Feeder #{feeder_num}")
            except (FileNotFoundError, json.JSONDecodeError):
                feeder_name = f"Feeder #{data['feeder']}"

            date = f"{data['month']}/{data['day']}"

            # Convert 1030 to 10:30
            hour = data['time'][:2]
            minute = data['time'][2:]
            amount = data['amount']

            return date, feeder_name, hour, minute, amount

    def get_cron_schedules() -> list[tuple]:
        cron_lines = get_cron_lines()
        feeding_jobs = []
        expiry_lookup = {}

        # --- PASS 1: Build Expiry Lookup ---
        for line in cron_lines:
            expiry_data = parse_cron_expiry_line(line)
            if expiry_data:
                date_str, feeder_name, hour, minute, amount_str = expiry_data

                # Convert amount to int to ensure it matches the integer from parse_cron_add_line
                try:
                    amount_val = int(amount_str)
                except ValueError:
                    amount_val = amount_str

                # Create a unique key for matching: (Name, Hour, Minute, Amount)
                key = (feeder_name, hour, minute, amount_val)
                expiry_lookup[key] = date_str

        # --- PASS 2: Parse Feeding Jobs and Match ---
        for line in cron_lines:
            feed_data = parse_cron_add_line(line)
            if feed_data:
                feeder_name, hour, minute, amount, note = feed_data

                # Check if there is an expiry scheduled for this exact job
                key = (feeder_name, hour, minute, amount)
                if key in expiry_lookup:
                    # Compute day_of_week
                    expiry_date = expiry_lookup[key]
                    expiry_day_of_week = convert_date_to_day(expiry_date)
                    # Update the note with the expiry date
                    note = f"Ends {expiry_day_of_week} {expiry_date}"

                feeding_jobs.append((feeder_name, hour, minute, amount, note))

        return feeding_jobs

    # --- FETCH SYSTEM SCHEDULES ---
    def get_system_schedules() -> list[tuple]:
        system_schedules = []
        for feeder in clean_data.values():
            for schedule in feeder['schedules']:
                # FIX: Split "HH:MM" so we have separate Hour/Minute
                time_str = schedule.get('time', "00:00")
                if ":" in time_str:
                    hour, minute = time_str.split(":")
                else:
                    hour, minute = "00", "00"

                # RETURN 5 ITEMS: (Name, Hour, Minute, Amount, Source)
                system_schedules.append(
                    (feeder['name'], hour, minute,
                     schedule['amount'], "Set in app")
                )
        return system_schedules

    # --- PRINT ALL SCHEDULES ---
    def print_all_schedules() -> list[tuple]:
        # Get lists from both sources (Both now have 5 items)
        cron_schedules: list[tuple] = get_cron_schedules()
        system_schedules: list[tuple] = get_system_schedules()
        all_schedules: list[tuple] = cron_schedules + system_schedules

        cups_per_unit = {1: "⅛ cup", 2: "¼ cup", 3: "⅜ cup", 4: "½ cup",
                         5: "⅝ cup", 6: "¾ cup", 7: "⅞ cup", 8: "1 cup"}

        # We create a NEW list for the final formatted output
        formatted_schedules = []

        for item in all_schedules:
            # UNPACK 5 ITEMS
            feeder_name, hour, minute, amount, source = item

            # Format Amount
            if str(amount).isdigit():
                amount_str: str = cups_per_unit.get(int(amount), f"{amount}")
            else:
                amount_str = "ERROR"

            # Combine Time for Display (and for petsafe_main compatibility)
            time_str = f"{hour}:{minute}"

            # Create 4-item tuple for the Table & Main Script
            formatted_schedules.append(
                (feeder_name, time_str, amount_str, source))

        # Update the main list to use the formatted version
        all_schedules = formatted_schedules

        # Print Header
        w_name, w_time, w_amount, w_type = 6, 5, 5, 15
        print("")
        print(
            f"{'Feeder':<{w_name}} | {'Time':<{w_time}} | {'Amt.':<{w_amount}} | {'Note':<{w_type}}")
        print("-" * (w_name + w_time + w_amount + w_type + 1))

        if not all_schedules:
            print("No feeder schedules found.")
            print("")
            return []
        else:
            # Sort by Time (index 1 is now "HH:MM")
            temp_rows = sorted(all_schedules, key=lambda x: x[0], reverse=True)
            rows = sorted(temp_rows, key=lambda x: x[1])

            for row in rows:
                if row[0] == "Under ***REMOVED***":
                    name = "***REMOVED***"
                else:
                    name = row[0]
                print(
                    f"{name:<{w_name}} | {row[1]:<{w_time}} | {row[2]:<{w_amount}} | {row[3]:<{w_type}}")
            print("")

            return rows

    # --- PRINT SCHEDULE ---
    all_schedules = print_all_schedules()
    return all_schedules


if __name__ == "__main__":
    clean_data = fetch_feeder_info()
    view_schedule(clean_data)
