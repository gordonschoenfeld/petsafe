#!/usr/bin/env python3

import re
import json
import renew_tokens               # Keep this here, even if not called.
import subprocess
import petsafe_smartfeed as sf
from datetime import datetime


# Run the token validation process, and wait for it to finish
subprocess.run(["python3", "renew_tokens.py"])

# Initialize globals to None
client = None
feeders_list = {}


def initialize_resources():
    # Loads tokens and connects to client. Moved to a function to prevent startup latency.
    global client, feeders_list

    # Load tokens
    try:
        # Update this path if necessary
        with open("tokens_petsafe.json", "r") as f:
            saved_tokens = json.load(f)
    except FileNotFoundError:
        print("ERROR: 'tokens_petsafe.json' not found. Please run auth_setup.py first.")
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
        hour = f"{time[:2]}"
        minute = f"{time[-2:]}"
        return hour, minute


def get_feeder_number_flex() -> int | str:
    feeder_number = input(
        "Enter feeder number: [1. Under ***REMOVED***, 2. ***REMOVED***, A. all]: ").strip().lower()
    # escape hatch
    if feeder_number in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # all option
    elif feeder_number in ['all', 'a']:
        return "all"
    elif feeder_number == '':
        print(f"⚠️ Interpreting as 'all'.")
        return "all"
    # option 1. under stairs
    elif feeder_number.lower().strip() in ['1', '1.', 'under stairs', 'us', 'u', 'under', 'stairs', 's']:
        return 1
    # option 2. island
    elif feeder_number.lower().strip() in ['2', '2.', 'island', 'i']:
        return 2
    # reject invalid feeder number
    else:
        print("Invalid feeder number. Please enter 1, 2, or A.")
        return get_feeder_number_flex()  # Retry


def get_amount() -> int | str:
    amount = input(
        "Enter units to feed (1 unit = 1/8 cup), or DEFAULT: ").strip().lower()
    # escape hatch
    if amount in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # default option
    if amount.lower() in ['default', 'd', 'auto', 'a']:
        return "default"
    if amount == '':
        print(f"⚠️ Interpreting as 'default'.")
        return "default"
    # reject invalid amount
    if (not amount.isdigit() or int(amount) < 1) and amount not in ['default', 'd', 'auto', 'a', '']:
        print("Invalid amount. Please enter a positive integer, or 'DEFAULT'.")
        return get_amount()  # Retry
    else:
        return int(amount)


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

    def validate_date(date_str: str, now=None) -> tuple[str]:
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
            f"Enter {clarifying_text} date (MM/DD), or 'NONE': ").strip().lower()
    else:
        raw_date_input = input(
            f"Enter date (MM/DD), or 'NONE': ").strip().lower()

    # escape hatch
    if raw_date_input in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # allow none
    if raw_date_input.strip().lower() in ['never', 'none', 'no', 'n', '']:
        return None

    # 1. VALIDATE the raw string (e.g., "8/9")
    # Do NOT pass a tuple here.
    if not validate_date(raw_date_input):
        print("Invalid format.")
        return None

    # 2. NORMALIZE after validation is successful
    # This turns "8/9" into ('08', '09')
    clean_date = normalize_date(raw_date_input)

    # return valid date
    return clean_date


def compute_date_diff(date1: tuple | str, date2: tuple | str) -> int | None:
    # 1. Convert Tuple inputs ('MM', 'DD') to String "MM/DD". subprocess.run cannot handle tuples directly.
    if isinstance(date1, tuple):
        date1 = f"{date1[0]}/{date1[1]}"

    if isinstance(date2, tuple):
        date2 = f"{date2[0]}/{date2[1]}"

    try:
        # 2. Run the external script
        result = subprocess.run(
            ['python3', 'compute_date_diff.py', date1, date2],  # Ensure python3
            capture_output=True,
            text=True,
            check=True
        )

        # 3. Return the result as an integer
        return int(result.stdout.strip())

    except subprocess.CalledProcessError as e:
        print(f"ERROR executing script: {e.stderr}")
        return None
    except ValueError:
        print(f"ERROR: Script returned non-integer: {result.stdout}")
        return None


# -- 👀 VIEW SCHEDULE FUNCTION --
def view_schedule(clean_data: dict) -> list[tuple]:
    from view_schedule import view_schedule
    return view_schedule(clean_data)


# -- ➕ ADD SCHEDULE FUNCTION --
def add_schedule(hour: str, minute: str, amount: int | str, feeder_number: int | str) -> bool:
    amount: str = str(amount)
    feeder_number: str = str(feeder_number)
    script_path: str = "./add_scheduled_feed.sh"

    # 1. Translate 'default' amount
    if amount == "default":
        amount = str(feeders_list[feeder_number]["default_amount"])

    try:
        # 2. Call the script with the arguments
        # The arguments are passed as a list: [Script, Arg1, Arg2, Arg3]
        result = subprocess.run(
            [script_path, hour, minute, feeder_number, amount],
            capture_output=True,  # Captures stdout and stderr
            text=True,            # Returns output as string instead of bytes
            check=True            # Raises CalledProcessError if script fails
        )

        # [DISABLED] # 3. Print the success output from the shell script
        # print("Request placed successfully!")
        # print("Output:\n", result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        # 4. Handle errors (e.g., script not found, permission denied)
        print(f"ERROR occurred while setting schedule!")
        print(f"ERROR Code: {e.returncode}")
        print(f"ERROR Message:\n{e.stderr}")
        return False

    except FileNotFoundError:
        print(f"ERROR: could not find the script at: {script_path}")
        return False


# -- 🌞 SET START FUNCTION --
def set_start(start_date: tuple[str], hour: str, minute: str, amount: int | str, feeder_number: int) -> bool:
    """
    Calls set_start.sh to schedule a self-destructing cron job.
    """
    script_path = "./set_start.sh"

    start_month, start_day = start_date
    # Variables are already separate now, no need to slice a time string
    target_hour = hour
    target_min = minute

    with open("feeders_general_info.json", "r") as f:
        feeders_list = json.load(f)

    # 1. Basic Validation
    if not (start_month.isdigit() and start_day.isdigit()):
        print("ERROR: Month and Day must be numbers.")
        return False
    if not (1 <= int(start_month) <= 12) or not (1 <= int(start_day) <= 31):
        print(f"ERROR: Invalid date {start_month}/{start_day}.")
        return False

    # 2. Handle 'default' amount
    if str(amount).lower() == 'default':
        amount = str(feeders_list[str(feeder_number)]["default_amount"])

    # 3. Call the Shell Script
    try:
        result = subprocess.run(
            [script_path, str(start_month), str(start_day), str(target_hour), str(target_min), str(
                feeder_number), str(amount)],
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to set start: {e.stderr.strip() or e.stdout.strip()}")
        return False

    except FileNotFoundError:
        print(f"ERROR: '{script_path}' not found.")
        return False


# -- 🌙 SET EXPIRY FUNCTION --
def set_expiry(expiry_date: tuple[str], hour: str, minute: str, amount: int | str, feeder_number: int) -> bool:
    """
    Calls set_expiry.sh to schedule a self-destructing cron job.
    """
    script_path = "./set_expiry.sh"

    expiry_month, expiry_day = expiry_date
    # Variables are already separate now
    target_hour = hour
    target_min = minute

    with open("feeders_general_info.json", "r") as f:
        feeders_list = json.load(f)

    # 1. Basic Validation
    if not (expiry_month.isdigit() and expiry_day.isdigit()):
        print("ERROR: Month and Day must be numbers.")
        return False

    if not (1 <= int(expiry_month) <= 12) or not (1 <= int(expiry_day) <= 31):
        print(f"ERROR: Invalid date {expiry_month}/{expiry_day}.")
        return False

    # 2. Handle 'default' amount
    if str(amount).lower() == 'default':
        amount = str(feeders_list[str(feeder_number)]["default_amount"])

    try:
        # 3. Call the Shell Script
        result = subprocess.run(
            [script_path, str(expiry_month), str(expiry_day), str(target_hour), str(target_min), str(
                feeder_number), str(amount)],
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to set expiry: {e.stderr.strip() or e.stdout.strip()}")
        return False

    except FileNotFoundError:
        print(f"ERROR: '{script_path}' not found.")
        return False


# -- 🔎 FIND SCHEDULE --
def find_schedule(hour: str, minute: str, feeder_number: int, clean_data: dict, all_schedules: dict) -> None:
    # 1. Resolve Feeder ID and Name
    feeder_id = get_id_by_number(clean_data, feeder_number)
    if not feeder_id:
        print(f"ERROR: Feeder number {feeder_number} not found.")
        return
    target_feeder_name = clean_data[feeder_id]['name']

    # 2. Construct the time string matches the format in all_schedules ("HH:MM")
    time = f"{hour}:{minute}"

    # 3. Find matches
    matching_result = [
        item for item in all_schedules
        if item[0] == target_feeder_name and item[1] == time
    ]

    if not matching_result:
        return None

    # NOTE format: matching_result=[('Under ***REMOVED***', '08:00', '¼ cup', '02/20 ~ 02/24')]
    # Instantiate vars
    matching_result_active: list = []
    matching_result_future: list = []
    matching_result_expiry: list = []

    # a. Current active schedules
    if matching_result[0][3] == "":
        matching_result_active: list = matching_result

    # b. Future matches
    future_regex = r"(\d{2}\/\d{2}).* ~"
    future_match = re.search(future_regex, matching_result[0][3])
    if future_match:
        matching_result_future: list = matching_result

    # c. Expiry matches
    expiry_regex = r"~ .*(\d{2}\/\d{2})"
    expiry_match = re.search(expiry_regex, matching_result[0][3])
    if expiry_match:
        matching_result_expiry: list = matching_result

    # d. Special case: if expiry but not future, add to active also
    if matching_result_expiry and not matching_result_future:
        matching_result_active: list = matching_result

    # 4. Check source (App vs Local)
    # Index [3] corresponds to the "Note/Source" column
    matching_result_app = [
        item for item in matching_result if item[3] == "Set in app"]

    matching_result_nonapp = [
        item for item in matching_result if item[3] != "Set in app"]

    # 5. Pass response
    match_blob = {'active': matching_result_active,
                  'future': matching_result_future,
                  'expiry': matching_result_expiry,
                  'nonapp': matching_result_nonapp,
                  'app': matching_result_app,
                  'time': time}
    return match_blob


# -- 🗑️ REMOVE SCHEDULE FUNCTION --
def remove_schedule(hour: str, minute: str, feeder_number: int, clean_data: dict, all_schedules: dict) -> None:
    # NOTE Schedule format: (feeder_name: str, time: str, amount: str, source: str)
    # 1. Fetch matching results
    matching_result = find_schedule(
        hour, minute, feeder_number, clean_data, all_schedules)

    # 2. Error out of no matches
    if matching_result is None:
        print(
            f"⚠️ ERROR: No schedule found at {hour}:{minute} for Feeder #{feeder_number}.")
        return

    # 3. Unpack matching results
    matching_result_active = matching_result['active']
    matching_result_future = matching_result['future']
    matching_result_expiry = matching_result['expiry']
    matching_result_nonapp = matching_result['nonapp']
    matching_result_app = matching_result['app']
    time = matching_result['time']

    # 4. Handle errors
    #    a. "Set in App" restriction: If we found it in the App but NOT locally, we can't delete it.
    if matching_result_app and not matching_result_nonapp:
        print(
            f"⚠️ ERROR: Cannot remove schedule at {time} for Feeder #{feeder_number}.")
        print(f"   (This schedule is managed by the PetSafe Cloud/App)")
        return

    # 5. Execute Removals
    def execute_deletion(script_name: str, feeder_number, hour, minute) -> bool:
        script_str = f"./{script_name}"
        try:
            result = subprocess.run(
                [script_str, str(feeder_number), str(hour), str(minute)],
                check=True,
                capture_output=True,
                text=True
            )
            return True

        except subprocess.CalledProcessError as e:
            print(
                f"Failed to remove schedule: {e.stderr.strip() or e.stdout.strip()}")
            return False

        except FileNotFoundError:
            print("ERROR: remove_scheduled_feed.sh not found.")
            return False

    if matching_result_expiry:
        execute_deletion("remove_future_expiry.sh",
                         feeder_number, hour, minute)

    if matching_result_active:
        execute_deletion("remove_scheduled_feed.sh",
                         feeder_number, hour, minute)

    if matching_result_future:
        execute_deletion("remove_future_start.sh",
                         feeder_number, hour, minute)


# --- 🌳 MAIN INPUT TREE ---
def task_input() -> None:
    action = input(
        "Select action: Add (A), Remove (R), View (V), Exit (X): ").strip().lower()

    # INPUT: ADD ACTION
    if action in ['add', 'a']:
        hour, minute = get_time()
        feeder_number = get_feeder_number_flex()
        amount = get_amount()
        start_date = get_date("start")
        expiry_date = get_date("final")
        todays_date = (datetime.now().strftime('%m'),
                       datetime.now().strftime('%d'))

        # 1. Perform checks
        #    a. validate that dates aren't over 180 days from now; if so, send back for re-input
        if start_date:
            start_days_from_today = compute_date_diff(
                todays_date, start_date)
            if start_days_from_today > 180:
                print(
                    f"ERROR: Start date is in past, or more than 180 days in the future.")
                task_input()
        if expiry_date:
            expiry_days_from_today = compute_date_diff(
                todays_date, expiry_date)
            if expiry_days_from_today > 180:
                print(
                    f"ERROR: Expiry date is in past, or more than 180 days in the future.")
                task_input()

        #    b. validate that range isn't inverted; if so, send back for re-input
        if start_date and expiry_date:
            date_diff = compute_date_diff(start_date, expiry_date)
            if date_diff < 0:
                print(f"ERROR: Start date is after end date.")
                task_input()

        #    c. if start date == today: return start date = None (for immediate effectiveness)
        if start_date == todays_date:
            start_date = ''

        # 2. Check for existing entry
        # TODO: check
        # TODO: if existing: prompt, with entry (allow exit)
        # TODO: if yes: perform removals, then proceed

        # 3. Execute
        #    a. if start date supplied, trigger set_start
        if start_date:
            if feeder_number == "all":
                set_start(start_date, hour, minute, amount, 1)
                set_start(start_date, hour, minute, amount, 2)
            else:
                set_start(start_date, hour, minute, amount, feeder_number)

        #    b. if no start date supplied: trigger now
        else:
            if feeder_number == "all":
                add_schedule(hour, minute, amount, 1)
                add_schedule(hour, minute, amount, 2)
            else:
                add_schedule(hour, minute, amount, feeder_number)

        #    c. if expiry date supplied, trigger set_expiry
        if expiry_date:
            if feeder_number == "all":
                set_expiry(expiry_date, hour, minute, amount, 1)
                set_expiry(expiry_date, hour, minute, amount, 2)
            else:
                set_expiry(expiry_date, hour, minute, amount, feeder_number)

        # 4. Show new schedules
        clean_data: dict = fetch_feeder_info()
        print(f"Updated schedules:")
        if clean_data:
            view_schedule(clean_data)

    # INPUT: REMOVE ACTION
    elif action in ['remove', 'r', 'rm', 'd', 'del', 'delete']:
        # Print current schedules, for user reference
        print("Current schedules:")
        clean_data: dict = fetch_feeder_info()
        if not clean_data:
            return

        all_schedules: list[tuple] = view_schedule(clean_data)

        # Prompt for machine & time to remove
        hour, minute = get_time()
        feeder_number = get_feeder_number_flex()

        # Call remove function. Validation is handled inside function.
        if feeder_number == "all":
            remove_schedule(hour, minute, 1, clean_data, all_schedules)
            remove_schedule(hour, minute, 2, clean_data, all_schedules)
        else:
            remove_schedule(hour, minute, feeder_number,
                            clean_data, all_schedules)

        # Show new schedules
        print(f"Updated schedules:")
        view_schedule(clean_data)

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
def main() -> None:
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
