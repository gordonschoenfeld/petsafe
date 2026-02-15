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
script_dir = os.path.dirname(os.path.abspath(__file__))
subfolder = os.path.join(script_dir, "config/")
info_file = os.path.join(subfolder, "feeders_config.json")

# --- MAIN LOGIC ---
try:
    with open(info_file, "r") as f:
        feeders_config = json.load(f)
except FileNotFoundError:
    print(f"Error: {subfolder}/{info_file} not found.")
    sys.exit(1)


def fetch_feeder_info() -> dict:
    clean_data: dict = {}
    id_to_num_map = {}

    try:
        # 1. Build the ID Map from config
        for num_key, data in feeders_config.items():
            # Ensure we capture the ID as an integer to match the API response
            cfg_id = data.get("id")
            if cfg_id:
                id_to_num_map[int(cfg_id)] = num_key

        # 2. Fetch from API
        feeders = client.feeders
        if not feeders:
            print("No feeders found on this account.")
            return {}

        # 3. Process each feeder
        for feeder in feeders:
            # Resolve the 'num' using the numbers map
            num = id_to_num_map.get(feeder.id)

            # If we find a feeder not in our config, skip it or label it unknown
            if not num:
                print(f"Warning: Found unconfigured feeder ID: {feeder.id}")
                continue

            clean_data[feeder.id] = {}
            clean_data[feeder.id]["feeder_number"] = num
            clean_data[feeder.id]["api_id"] = feeder.data.get(
                "thing_name", "Unknown")

            # Load config data safely
            clean_data[feeder.id]["name"] = feeders_config[num]["name"]
            clean_data[feeder.id]["default_amount"] = feeders_config[num]["default_amount"]

            # Display schedules
            clean_data[feeder.id]["schedules"] = []
            for schedule in feeder.data["schedules"]:
                clean_data[feeder.id]["schedules"].append({
                    "time": schedule["time"],
                    "amount": schedule["amount"],
                    "id": schedule["id"]
                })

            clean_data[feeder.id]["schedules"].sort(key=lambda x: x['time'])
            clean_data[feeder.id]["slow_feed"] = False

        return clean_data

    except Exception as e:
        print(f"\nAn error occurred in fetch_feeder_info: {e}")
        return {}


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
                return []

            return [line for line in result.stdout.splitlines() if line.strip()]

        except FileNotFoundError:
            print("Error: 'crontab' command not found.")
            sys.exit(1)

    def parse_cron_add_line(line) -> tuple | None:
        # Parse active feed_now.py lines
        target_script = "feed_now.py"
        parts = line.split()

        if len(parts) < 6 or target_script not in line:
            return None

        minute = parts[0].zfill(2)
        hour = parts[1].zfill(2)

        try:
            script_idx = parts.index(target_script)
            feeder_id = parts[script_idx + 1]
            amount = int(parts[script_idx + 2])
        except (ValueError, IndexError):
            return None

        # Resolve Name
        feeder_info = feeders_config.get(str(feeder_id), {})
        feeder_name = feeder_info.get("name", f"Feeder #{feeder_id}")

        return feeder_name, hour, minute, amount, ""

    def parse_cron_start_line(line) -> tuple | None:
        """
        Parses future start jobs (add_scheduled_feed.sh).
        Ex: ... add_scheduled_feed.sh <HOUR> <MIN> <FEEDER> <AMOUNT> ...
        """
        if "add_scheduled_feed.sh" not in line:
            return None

        # Regex to capture arguments: Hour, Min, Feeder, Amount
        # Handles full paths like /bin/bash ... /add_scheduled_feed.sh 10 01 1 2
        pattern = re.compile(
            r"add_scheduled_feed\.sh\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)")
        match = pattern.search(line)

        if not match:
            return None

        hour_arg, min_arg, feeder_arg, amount_arg = match.groups()

        # Parse Start Date from the cron fields (Min Hour Day Month ...)
        # We grab fields index 2 (Day) and 3 (Month)
        parts = line.split()
        if len(parts) < 5:
            return None

        start_day = parts[2]
        start_month = parts[3]
        start_date_str = f"{start_month.zfill(2)}/{start_day.zfill(2)}"

        # Resolve Name
        feeder_info = feeders_config.get(str(feeder_arg), {})
        feeder_name = feeder_info.get("name", f"Feeder #{feeder_arg}")

        return feeder_name, hour_arg.zfill(2), min_arg.zfill(2), int(amount_arg), start_date_str

    def parse_cron_expiry_line(line) -> tuple | None:
        # Example: 59 23 10 02 * /usr/local/bin/python3 -c 'import time,random; time.sleep(random.random() * 20)' && crontab -l | grep -E -v '^34[ \t]+12[ \t]+.*feed_now.py 1 1' | grep -F -v '#EXPIRY_AUTO_REMOVE_F1_A1_at_1234' | crontab - #EXPIRY_AUTO_REMOVE_F1_A1_at_1234
        # Define the pattern with named groups
        pattern = re.compile(
            r"^59 23 (?P<day>\d+) (?P<month>\d+) \* .*? #EXPIRY_AUTO_REMOVE_F(?P<feeder>\d+)_A(?P<amount>[^_]+)_at_(?P<time>\d{4})$")

        match = pattern.search(line)
        if match:
            data = match.groupdict()
            feeder_num: str = str(data['feeder'])
            feeder_info = feeders_config.get(feeder_num, {})
            feeder_name: str = feeder_info.get('name', f"Feeder #{feeder_num}")

            date = f"{data['month']}/{data['day']}"

            # Convert 1030 to 10:30
            hour = data['time'][:2]
            minute = data['time'][2:]
            amount = data['amount']

            return date, feeder_name, hour, minute, amount
        return None

    def get_cron_schedules() -> list[tuple]:
        cron_lines = get_cron_lines()
        feeding_jobs = []
        expiry_lookup = {}

        # --- PASS 1: Build Expiry Lookup ---
        for line in cron_lines:
            expiry_data = parse_cron_expiry_line(line)
            if expiry_data:
                date_str, feeder_name, hour, minute, amount_str = expiry_data
                try:
                    amount_val = int(amount_str)
                except ValueError:
                    amount_val = amount_str

                # Key: (Name, Hour, Minute, Amount)
                key = (feeder_name, hour, minute, amount_val)
                expiry_lookup[key] = date_str

        # --- PASS 2: Active Feeding Jobs ---
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
                    note = f"~ {expiry_day_of_week} {expiry_date}"

                feeding_jobs.append((feeder_name, hour, minute, amount, note))

        # --- PASS 3: Future Start Jobs ---
        for line in cron_lines:
            start_data = parse_cron_start_line(line)
            if start_data:
                feeder_name, hour, minute, amount, start_date = start_data
                key = (feeder_name, hour, minute, amount)

                # Check for Expiry
                if key in expiry_lookup:
                    expiry_date = expiry_lookup[key]
                    # Format: 02/10 - 02/15
                    note = f"{start_date} ~ {expiry_date}"
                else:
                    # Format: Mon 02/10 ~
                    start_weekday = convert_date_to_day(start_date)
                    note = f"{start_weekday} {start_date} ~"

                feeding_jobs.append((feeder_name, hour, minute, amount, note))

        return feeding_jobs

    # --- FETCH SYSTEM SCHEDULES ---
    def get_system_schedules() -> list[tuple]:
        system_schedules = []
        for feeder in clean_data.values():
            for schedule in feeder['schedules']:
                time_str = schedule.get('time', "00:00")
                if ":" in time_str:
                    hour, minute = time_str.split(":")
                else:
                    hour, minute = "00", "00"

                system_schedules.append(
                    (feeder['name'], hour, minute,
                     schedule['amount'], "Set in app")
                )
        return system_schedules

    # --- PRINT ALL SCHEDULES ---
    def print_all_schedules() -> list[tuple]:
        cron_schedules = get_cron_schedules()
        system_schedules = get_system_schedules()
        all_schedules = cron_schedules + system_schedules

        cups_per_unit = {1: "⅛ cup", 2: "¼ cup", 3: "⅜ cup", 4: "½ cup",
                         5: "⅝ cup", 6: "¾ cup", 7: "⅞ cup", 8: "1 cup"}

        formatted_schedules = []

        for item in all_schedules:
            feeder_name, hour, minute, amount, source = item

            if str(amount).isdigit():
                amount_str: str = cups_per_unit.get(int(amount), f"{amount}")
            else:
                amount_str = "ERROR"

            time_str = f"{hour}:{minute}"

            # Create 4-item tuple for output
            formatted_schedules.append(
                (feeder_name, time_str, amount_str, source))

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
            # Sort by Time
            temp_rows = sorted(all_schedules, key=lambda x: x[0], reverse=True)
            rows = sorted(temp_rows, key=lambda x: x[1])

            for row in rows:
                print(
                    f"{row[0]:<{w_name}} | {row[1]:<{w_time}} | {row[2]:<{w_amount}} | {row[3]:<{w_type}}")
            print("")

            return rows

    # --- PRINT SCHEDULE ---
    return print_all_schedules()


if __name__ == "__main__":
    clean_data = fetch_feeder_info()
    view_schedule(clean_data)
