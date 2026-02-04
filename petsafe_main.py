#!/usr/bin/env python3

import re
import sys
import json
import requests
import subprocess
import petsafe_smartfeed as sf
from datetime import datetime


# --- START MONKEY PATCH ---
def patched_refresh_tokens(self):
    """
    Patched method to handle missing RefreshToken in AWS response.
    """
    # 1. Hardcode the PetSafe Client ID (Public Mobile App ID)
    CLIENT_ID = "18hpp04puqmgf5nc6o474lcp2g"

    # 2. Construct the payload WITHOUT the Secret Hash
    # (This client is public, so it doesn't use a client secret)
    data = {
        "ClientId": CLIENT_ID,
        "AuthFlow": "REFRESH_TOKEN_AUTH",
        "AuthParameters": {
            "REFRESH_TOKEN": self.refresh_token
        },
    }

    headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    }

    # 3. Send Request to AWS Cognito
    response = requests.post(
        "https://cognito-idp.us-east-1.amazonaws.com/",
        json=data,
        headers=headers
    ).json()

    # 4. Handle Response
    if "AuthenticationResult" in response:
        self.id_token = response["AuthenticationResult"]["IdToken"]
        self.access_token = response["AuthenticationResult"]["AccessToken"]

        # THE FIX: Use .get() so we don't crash if AWS doesn't send a new RefreshToken
        self.refresh_token = response["AuthenticationResult"].get(
            "RefreshToken", self.refresh_token)
    else:
        # If AWS returns an error, print it clearly
        print("\n--- AWS COGNITO ERROR ---")
        print(json.dumps(response, indent=2))
        raise Exception("Failed to refresh tokens. See AWS error above.")


sf.PetSafeClient.refresh_tokens = patched_refresh_tokens
# --- END MONKEY PATCH ---

# Initialize globals to None
client = None
feeders_list = {}


def initialize_resources():
    # Loads tokens and connects to client. Moved to a function to prevent startup latency.
    global client, feeders_list

    # Load tokens
    try:
        # Update this path if necessary
        with open("petsafe_tokens.json", "r") as f:
            saved_tokens = json.load(f)
    except FileNotFoundError:
        print("Error: 'petsafe_tokens.json' not found. Please run auth_setup.py first.")
        exit()

    # Initialize client (The slow part: Network connection)
    client = sf.PetSafeClient(
        email=saved_tokens["email"],
        id_token=saved_tokens["id_token"],
        refresh_token=saved_tokens["refresh_token"],
        access_token=saved_tokens["access_token"]
    )

    # Fetch default amounts per feeder
    with open("feeders_general_info.json", "r") as f:
        feeders_list = json.load(f)


# --- FETCH FEEDER INFO & GENERATE `clean_data` DICT ---
def fetch_feeder_info() -> dict:
    clean_data: dict = {}

    try:
        feeders = client.feeders
        if not feeders:
            print("No feeders found on this account.")
            return
        for feeder in feeders:
            clean_data[feeder.id] = {}
            # id: ***REMOVED*** is Under ***REMOVED***
            if feeder.id == ***REMOVED***:
                num = "1"
            # id: ***REMOVED*** is ***REMOVED***
            elif feeder.id == ***REMOVED***:
                num = "2"
            clean_data[feeder.id]["feeder_number"] = num
            clean_data[feeder.id]["api_id"] = feeder.data["thing_name"]
            clean_data[feeder.id]["name"] = feeders_list[num]["name"]
            clean_data[feeder.id]["default_amount"] = feeders_list[num]["default_amount"]
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
        print(f"\nAn error occurred: {e}")
        # Print traceback only if needed for debugging:
        # import traceback
        # traceback.print_exc()


# --- TRANSLATE FEEDER NUMBER INTO ID ---
def get_id_by_number(clean_data, target_number) -> int | None:
    # Force target to a string to match the data format ('1' vs 1)
    target_number: str | int = str(target_number)

    for feeder_id, data in clean_data.items():
        if data['feeder_number'] == target_number:
            return feeder_id
    return None  # Return None if not found


# --- INPUT VALIDATION SUB-FUNCTIONS ---
def get_time() -> str:
    time = input(
        "Enter feed time (24-hour format HH:MM): ").strip().lower()
    # escape hatch
    if time in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # reject invalid time format
    if not re.match(r'^([01]\d|2[0-3]):?([0-5]\d)$', time):
        print("Invalid time format. Please use HH:MM (00:00 to 23:59).")
        return get_time()  # Retry
    # return valid time
    else:
        time = f"{time[:2]}:{time[-2:]}"
        return time


def get_feeder_number_flex() -> int | str:
    feeder_number = input(
        "Enter feeder number: [1. Under ***REMOVED***, 2. ***REMOVED***, A. all]: ").strip().lower()
    # escape hatch
    if feeder_number in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # reject invalid feeder number
    if feeder_number not in ['1', '2', 'a', 'all']:
        print("Invalid feeder number. Please enter 1, 2, or A.")
        return get_feeder_number_flex()  # Retry
    # all option
    if feeder_number in ['all', 'a']:
        return "all"
    else:
        return int(feeder_number)


def get_feeder_number_single() -> int:
    feeder_number = input(
        "Enter feeder number to add schedule to: [1 Under ***REMOVED***, 2 ***REMOVED***]: ").strip().lower()
    # escape hatch
    if feeder_number in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # reject invalid feeder number
    if feeder_number not in ['1', '2']:
        print("Invalid feeder number. Please enter 1 or 2 only.")
        return get_feeder_number_single()  # Retry
    else:
        return int(feeder_number)


def get_amount() -> int | str:
    amount = input(
        "Enter units to feed (1 unit = 1/8 cup), or AUTO: ").strip().lower()
    # escape hatch
    if amount in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # reject invalid amount
    if (not amount.isdigit() or int(amount) < 1) and amount not in ['auto', 'a']:
        print("Invalid amount. Please enter a positive integer, or 'AUTO'.")
        return get_amount()  # Retry
    # auto option
    if amount.lower() in ['auto', 'a']:
        return "auto"
    else:
        return int(amount)


def get_date(clarifying_text: str = None) -> tuple[str] | None:
    def normalize_date(date_str: str) -> tuple[str]:
        # Regex Breakdown:
        # 1. (0?[1-9]|1[0-2]) : Capture Group 1 (Month) - 1-12, optional leading zero
        # 2. \/?              : Optional Slash (ignored)
        # 3. (0?[1-9]|[12]\d|3[01]) : Capture Group 2 (Day) - 1-31, optional leading zero

        match = re.match(
            r'^(0?[1-9]|1[0-2])\/?(0?[1-9]|[12]\d|3[01])$', date_str)

        if match:
            month, day = match.groups()

            # Enforce 4-digit logic: if input was "0809", regex splits it correctly.
            # If input was "89", regex might match (8, 9), but that is usually ambiguous.
            # This regex assumes standard separators or clear 4-digit blocks.

            # Return tuple with leading zeros
            return (month.zfill(2), day.zfill(2))
        else:
            return None

    def validate_date(date_str: str, now=None):
        # Regex Breakdown (3 Distinct Branches):
        # 1. Slash Required:  8/9, 08/09, 12/31
        # 2. 4-Digit Strict:  0809, 1231
        # 3. 2-Digit Strict:  12 (splits to 1/2), 89 (splits to 8/9)
        #    Note: Uses [1-9] to ensure we don't match "10" (Day 0 is invalid)

        pattern = (
            r'^(?:'
            r'(0?[1-9]|1[0-2])\/(0?[1-9]|[12]\d|3[01])|'  # Branch 1: Slash
            r'(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])|'      # Branch 2: 4-Digit
            r'([1-9])([1-9])'                             # Branch 3: 2-Digit
            r')$'
        )

        match = re.match(pattern, date_str)

        if not match:
            raise ValueError(
                f"Invalid format: '{date_str}'. Accepted: M/D, MMDD, or MD.")

        # Extract groups. The regex has 6 groups total (2 per branch).
        # We find the pair that isn't None.
        g = match.groups()
        month_str = g[0] or g[2] or g[4]
        day_str = g[1] or g[3] or g[5]

        month, day = int(month_str), int(day_str)

        # --- Standard Date Logic (Same as before) ---
        if now is None:
            now = datetime.now()

        try:
            candidate_date = datetime(now.year, month, day, 12, 0, 0)
        except ValueError:
            if month == 2 and day == 29:
                candidate_date = None
            else:
                raise ValueError(f"Invalid calendar date: {month}/{day}")

        if candidate_date is None or candidate_date < now:
            try:
                candidate_date = datetime(now.year + 1, month, day, 12, 0, 0)
            except ValueError:
                raise ValueError(
                    f"Date {month}/{day} does not exist in the upcoming year.")

        return candidate_date

    if clarifying_text:
        raw_date_input = input(
            f"Enter {clarifying_text} date (MM/DD): ").strip().lower()
    else:
        raw_date_input = input(f"Enter date (MM/DD): ").strip().lower()

    # escape hatch
    if raw_date_input in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # allow none
    if raw_date_input.strip().lower() in ['none', 'no', 'n']:
        return None

    # 1. VALIDATE the raw string (e.g., "8/9")
    # Do NOT pass a tuple here.
    if not validate_date(raw_date_input):
        print("Invalid format.")
        return None

    # 2. NORMALIZE after validation is successful
    # This turns "8/9" into ('08', '09') or a datetime object
    clean_date = normalize_date(raw_date_input)

    # return valid date
    print(f"DEBUG | {clean_date=}")
    return clean_date


# -- 👀 VIEW SCHEDULE FUNCTION --
def view_schedule(clean_data: dict) -> list[tuple]:
    # TODO: display the exp date

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
        Parses a single cron line to extract time, feeder, and amount.
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
        time_str = f"{hour}:{minute}"

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

        return feeder_name, time_str, amount, ""

    def parse_cron_expiry_line(line) -> tuple | None:
        log_line = line

        # Define the pattern with named groups for easy extraction
        pattern = re.compile(
            r"^59 23 (?P<day>\d+) (?P<month>\d+) \* .*? # EXPIRY_AUTO_REMOVE_F(?P<feeder>\d+)_A(?P<amount>[^_]+)_T(?P<time>\d{4})$")

        match = pattern.search(log_line)

        if match:
            data = match.groupdict()

            with open("feeders_general_info.json", "r") as f:
                feeders_list = json.load(f)

            # Assemble output vars
            feeder_num: str = str(data['feeder'])
            feeder_name: str = feeders_list[feeder_num]['name']
            date = f"{data['month']}/{data['day']}"
            # Convert 1030 to 10:30
            time_str = f"{data['time'][:2]}:{data['time'][2:]}"
            amount = data['amount']

            return date, feeder_name, time_str, amount

    def get_cron_schedules() -> list[tuple]:
        cron_schedules = []
        cron_lines = get_cron_lines()
        for line in cron_lines:
            parsed = parse_cron_add_line(line)
            if parsed:
                cron_schedules.append(parsed)
        return cron_schedules

        # TODO merge in lookups of parse_cron_expiry_line(line)

    # --- FETCH SYSTEM SCHEDULES ---
    def get_system_schedules() -> list[tuple]:
        system_schedules = []
        for feeder in clean_data.values():
            for schedule in feeder['schedules']:
                system_schedules.append(
                    (feeder['name'], schedule['time'], schedule['amount'], "Set in app"))
        return system_schedules

    # --- PRINT ALL SCHEDULES ---
    def print_all_schedules() -> list[tuple]:
        # NOTE Schedule format: (feeder_name: str, time: str, amount: str, source: str)

        # Get lists from both sources and combine both lists
        cron_schedules: list[tuple] = get_cron_schedules()
        system_schedules: list[tuple] = get_system_schedules()
        all_schedules: list[tuple] = cron_schedules + system_schedules
        complete_symbol: str = "●"    # alts: █ ● ▰
        incomplete_symbol: str = "○"  # alts: ░ ○ ▱

        # Convert amount from units to cups for display
        cups_per_unit = {1: "1/8 cup", 2: "1/4 cup", 3: "3/8 cup", 4: "1/2 cup",
                         5: "5/8 cup", 6: "3/4 cup", 7: "7/8 cup", 8: "1 cup"}
        for i in range(len(all_schedules)):
            feeder_name, time, amount, source = all_schedules[i]
            if str(amount).isdigit():
                amount_str: str = cups_per_unit.get(amount, f"{amount}")
                amount_bar = int(amount) * complete_symbol \
                    + (8 - int(amount)) * incomplete_symbol
            else:
                amount_str = "ERROR"
            all_schedules[i] = (
                feeder_name, time, amount_str, amount_bar, source)

        # --- PRINT TABLE ---
        # Define column widths
        w_name, w_time, w_amount, w_type = 20, 7, 8, 11

        # Print Header
        print("")
        print(f"{'Feeder Name':<{w_name}} | {'Time':<{w_time}} | {'Amount':<{w_amount + 8}} | {'Note':<{w_type}}")
        print("-" * (w_name + w_time + w_amount + w_type + 18))

        if not all_schedules:
            print("No feeder schedules found.")
        else:
            # Sort by Time asc, and secondarily by feeder name desc
            temp_rows = sorted(all_schedules,
                               key=lambda x: x[0], reverse=True)
            rows = sorted(temp_rows, key=lambda x: x[1])

            for row in rows:
                print(
                    f"{row[0]:<{w_name}} | {row[1]:<{w_time}} | {row[2]} {row[3]:<{w_amount}} | {row[4]:<{w_type}}")
        print("")

        return all_schedules

    # --- MAIN VIEW SCHEDULE LOGIC ---
    all_schedules = print_all_schedules()
    return all_schedules


# -- ➕ ADD SCHEDULE FUNCTION --
def add_schedule(time: str, amount: int | str, feeder_number: int | str) -> None:
    amount: str = str(amount)
    feeder_number: str = str(feeder_number)
    script_path: str = "./add_scheduled_feed.sh"

    # 1. Translate 'auto' amount
    if amount == "auto":
        amount = str(feeders_list[feeder_number]["default_amount"])

    try:
        # 2. Call the script with the arguments
        # The arguments are passed as a list: [Script, Arg1, Arg2, Arg3]
        result = subprocess.run(
            [script_path, time, feeder_number, amount],
            capture_output=True,  # Captures stdout and stderr
            text=True,            # Returns output as string instead of bytes
            check=True            # Raises CalledProcessError if script fails
        )

        # 3. Print the success output from the shell script
        print("Request placed successfully!")
        print("Output:\n", result.stdout)

    except subprocess.CalledProcessError as e:
        # 4. Handle errors (e.g., script not found, permission denied)
        print(f"Error occurred while setting schedule!")
        print(f"Error Code: {e.returncode}")
        print(f"Error Message:\n{e.stderr}")

    except FileNotFoundError:
        print(f"Error: could not find the script at: {script_path}")


# -- ☠️ SET EXPIRY FUNCTION --
def set_expiry(kill_date: tuple[str], time: str, amount: int | str, feeder_number: int) -> bool:
    """
    Calls set_expiry.sh to schedule a self-destructing cron job.

    Args:
        month (str): Month as "MM" or "M" (e.g., "02" or "2").
        day (str): Day as "DD" or "D" (e.g., "15" or "5").
        feeder_number (int): 1 or 2.
        amount (int | str): The amount to stop feeding (e.g., 5 or "auto").
    """
    script_path = "./set_expiry.sh"

    kill_month, kill_day = kill_date
    target_hour: str = time[:2]
    target_min: str = time[-2:]

    # 1. Basic Validation (Optional, but saves a shell call)
    if not (kill_month.isdigit() and kill_day.isdigit()):
        print("❌ Error: Month and Day must be numbers.")
        return False

    if not (1 <= int(kill_month) <= 12) or not (1 <= int(kill_day) <= 31):
        print(f"❌ Error: Invalid date {kill_month}/{kill_day}.")
        return False

    # 2. Handle 'auto' amount if passed
    # TODO: change to real interpretation
    if str(amount).lower() in ["auto", "a"]:
        print("❌ Error: Expiry requires a specific amount (e.g., 1, 2, 5). 'Auto' is ambiguous.")
        return False

    try:
        # 3. Call the Shell Script
        # Arguments: ./set_expiry.sh <kill_month> <kill_day> <target_hour> <target_min> <feeder_num> <amount>
        result = subprocess.run(
            [script_path, str(kill_month), str(kill_day), str(target_hour), str(target_min), str(
                feeder_number), str(amount)],
            capture_output=True,
            text=True,
            check=True
        )

        # 4. Success Feedback
        print(f"Success: {result.stdout.strip()}")
        return True

    except subprocess.CalledProcessError as e:
        # 5. Error Feedback
        print(f"Failed to set expiry: {e.stderr.strip() or e.stdout.strip()}")
        return False

    except FileNotFoundError:
        print(
            f"Error: '{script_path}' not found. Make sure it exists and is executable.")
        return False


# -- 🗑️ REMOVE SCHEDULE FUNCTION --
def remove_schedule(time: str, feeder_number: int, clean_data: dict, all_schedules: dict) -> None:
    # NOTE Schedule format: (feeder_name: str, time: str, amount: str, source: str)

    # Validation
    feeder_id: int = get_id_by_number(clean_data, feeder_number)

    matching_result_app = [item for item in all_schedules if item[0] == clean_data[feeder_id]['name'] and item[1]
                           == time and item[4] == "Set in app"]
    if matching_result_app:
        print(
            f"❌ Cannot remove schedule at {time} for Feeder #{feeder_number}.")
        print(f"Please remove it via the PetSafe SmartFeed app 📲.")
        return

    matching_result = [item for item in all_schedules if item[0] == clean_data[feeder_id]['name'] and item[1]
                       == time]
    if not matching_result:
        print(
            f"❌ No schedule found at {time} for Feeder #{feeder_number}. Cannot remove.")
        return

    # TODO: handle duplicate schedules at same time?

    """
    Calls the remove_scheduled_feed.sh script to delete a specific cron job.
    Returns True if successful, False if the job wasn't found or an error occurred.
    """
    try:
        # We use check=True so that if the bash script exits with 1,
        # it raises a CalledProcessError automatically.
        result = subprocess.run(
            ["./remove_scheduled_feed.sh", str(feeder_number), str(time)],
            check=True,
            capture_output=True,
            text=True
        )

        print(f"Success: {result.stdout.strip()}")
        return True

    except subprocess.CalledProcessError as e:
        # This block catches the 'exit 1' from your bash script
        print(
            f"Failed to remove schedule: {e.stderr.strip() or e.stdout.strip()}")
        return False

    except FileNotFoundError:
        print("Error: remove_scheduled_feed.sh not found. Check the file path.")
        return False


# --- 🌳 MAIN INPUT TREE FUNCTION ---
def task_input() -> None:
    action = input(
        "Select action: Add (A), Remove (R), View (V), Exit (X): ").strip().lower()

    # INPUT: ADD ACTION
    if action in ['add', 'a']:
        time = get_time()
        feeder_number = get_feeder_number_flex()
        amount = get_amount()
        kill_date = get_date("expiration")

        if feeder_number == "all":
            add_schedule(time, amount, 1)
            add_schedule(time, amount, 2)
        else:
            add_schedule(time, amount, feeder_number)

        # if kill date supplied, trigger set_expiry
        if kill_date:
            if feeder_number == "all":
                set_expiry(kill_date, time, amount, 1)
                set_expiry(kill_date, time, amount, 2)
            else:
                set_expiry(kill_date, time, amount, feeder_number)

    # INPUT: REMOVE ACTION
    elif action in ['remove', 'r', 'rm', 'd', 'del', 'delete']:
        # Print current schedules, for user reference
        print("Current schedules:")
        clean_data: dict = fetch_feeder_info()
        all_schedules: list[tuple] = view_schedule(clean_data)

        # Prompt for machine & time to remove
        time = get_time()
        feeder_number = get_feeder_number_flex()

        # Call remove function. Validation is handled inside function.
        if feeder_number == "all":
            remove_schedule(time, 1, clean_data, all_schedules)
            remove_schedule(time, 2, clean_data, all_schedules)
        else:
            remove_schedule(time, feeder_number, clean_data, all_schedules)

    # INPUT: VIEW ACTION
    elif action in ['view', 'v', 'list', 'show']:
        view_schedule(fetch_feeder_info())

    # INPUT: EXIT ACTION
    elif action in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()

    # OTHER: reject invalid action
    else:
        print("Invalid action. Please enter A, R, V, or X.")
        return task_input()  # Retry


# --- 🏡 MAIN FUNCTION ---
def main():
    # 1. Print timestamp immediately
    print("================================")
    print("⭐️ RUN TIME:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("================================")
    print("")

    # 2. Now connect to the internet/load files, with the "Initializing client" message to be overwritten by the actual next line.
    print("Initializing client...", end="\r")  # Optional: Status indicator
    initialize_resources()

    # 3. Proceed
    task_input()


# --- 🏠 RUN MAIN FUNCTION ---
if __name__ == "__main__":
    main()
