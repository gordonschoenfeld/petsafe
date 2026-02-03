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


# Apply the patch
sf.PetSafeClient.refresh_tokens = patched_refresh_tokens
# --- END MONKEY PATCH ---


# Load tokens
try:
    with open("/Users/gordonschoenfeld/Python/PetSafe/petsafe_tokens.json", "r") as f:
        saved_tokens = json.load(f)
except FileNotFoundError:
    print("Error: 'petsafe_tokens.json' not found. Please run auth_setup.py first, and ensure it is in the correct directory.")
    exit()

# Print timestamp
print("RUN TIME:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=============================")
print("")

# Initialize client
client = sf.PetSafeClient(
    email=saved_tokens["email"],
    id_token=saved_tokens["id_token"],
    refresh_token=saved_tokens["refresh_token"],
    access_token=saved_tokens["access_token"]
)
# This is needed to know the default amounts per feeder.
with open("feeders_general_info.json", "r") as f:
    feeders_list = json.load(f)


# GET FEEDER INFO & GENERATE `clean_data` DICT
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


def get_id_by_number(clean_data, target_number) -> int | None:
    # Force target to a string to match the data format ('1' vs 1)
    target_number = str(target_number)

    for feeder_id, data in clean_data.items():
        if data['feeder_number'] == target_number:
            return feeder_id
    return None  # Return None if not found


# --- INPUT VALIDATION SUB-FUNCTIONS ---
def get_time() -> str:
    time = input(
        "Enter feed time (24-hour format HH:MM): ").strip()
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
        "Enter feeder number: [1. Under ***REMOVED***, 2. ***REMOVED***, A. all]: ").strip()
    # reject invalid feeder number
    if feeder_number.lower() not in ['1', '2', 'a', 'all']:
        print("Invalid feeder number. Please enter 1, 2, or A.")
        return get_feeder_number_flex()  # Retry
    if feeder_number.lower() in ['all', 'a']:
        return "all"
    else:
        return int(feeder_number)


def get_feeder_number_single() -> int:
    feeder_number = input(
        "Enter feeder number to add schedule to: [1 Under ***REMOVED***, 2 ***REMOVED***]: ").strip()
    # reject invalid feeder number
    if feeder_number not in ['1', '2']:
        print("Invalid feeder number. Please enter 1 or 2 only.")
        return get_feeder_number_single()  # Retry
    else:
        return int(feeder_number)


def get_amount() -> int | str:
    amount = input(
        "Enter units to feed (1 unit = 1/8 cup), or AUTO: ").strip()
    # reject invalid amount
    if not amount.isdigit() or int(amount) < 1 and amount not in ['auto', 'AUTO', 'Auto', 'a', 'A']:
        print("Invalid amount. Please enter a positive integer, or 'AUTO'.")
        return get_amount()  # Retry
    if amount.lower() in ['auto', 'a']:
        return "auto"
    else:
        return int(amount)


# -- VIEW SCHEDULE FUNCTION --
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

    def parse_cron_line(line) -> tuple | None:
        """
        Parses a single cron line to extract time, feeder, and amount.
        Assumes format: MIN HOUR * * * python_path script_path FEEDER_ID AMOUNT
        """
        # The name of the script we are looking for in the cron list
        target_script = "feed_now.py"

        parts = line.split()

        # Basic check: Cron lines usually have at least 5 time fields + command
        if len(parts) < 6:
            return None

        # Check if this line is running our target script
        if target_script not in line:
            return None

        # Extract Time
        minute = parts[0].zfill(2)  # 0 -> 00
        hour = parts[1].zfill(2)   # 8 -> 08
        time_str = f"{hour}:{minute}"

        # Extract Arguments
        # Based on set_schedule.sh, arguments are the LAST two items: [ID, AMOUNT]
        try:
            amount = int(parts[-1])
            feeder_id = parts[-2]
        except IndexError:
            return None

        # Lookup friendly name, default to "Feeder #ID" if not in dict
        with open("feeders_general_info.json", "r") as f:
            feeders_list = json.load(f)
        feeder_name = feeders_list.get(feeder_id, {}).get(
            "name", f"Feeder #{feeder_id}")

        return feeder_name, time_str, amount, ""

    def get_cron_schedules() -> list[tuple]:
        cron_schedules = []
        cron_lines = get_cron_lines()
        for line in cron_lines:
            parsed = parse_cron_line(line)
            if parsed:
                cron_schedules.append(parsed)
        return cron_schedules

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
        all_schedules_display: list[tuple] = cron_schedules + system_schedules
        all_schedules_clean: list[tuple] = all_schedules_display

        # Convert amount from units to cups for display
        cups_per_unit = {1: "1/8 cup", 2: "1/4 cup", 3: "3/8 cup", 4: "1/2 cup",
                         5: "5/8 cup", 6: "3/4 cup", 7: "7/8 cup", 8: "1 cup"}
        for i in range(len(all_schedules_display)):
            feeder_name, time, amount, source = all_schedules_display[i]
            if str(amount).isdigit():
                amount_str: str = cups_per_unit.get(amount, f"{amount}")
                amount_str += " [" \
                    + int(amount) * "█" + (8 - int(amount)) * "-" \
                    + "]"
            else:
                amount_str = "ERROR"
            all_schedules_display[i] = (feeder_name, time, amount_str, source)

        # --- PRINT TABLE ---
        # Define column widths
        # TODO: add bar graph of how much each feeding is [XX      ]

        w_name, w_time, w_amount, w_type = 20, 7, 18, 11

        # Print Header
        print("")
        print(f"{'Feeder Name':<{w_name}} | {'Time':<{w_time}} | {'Amount':<{w_amount}} | {'Note':<{w_type}}")
        print("-" * (w_name + w_time + w_amount + w_type + 9))

        if not all_schedules_display:
            print("No feeder schedules found.")
        else:
            # Sort by Time asc, and secondarily by feeder name desc
            temp_rows = sorted(all_schedules_display,
                               key=lambda x: x[0], reverse=True)
            rows = sorted(temp_rows, key=lambda x: x[1])

            for row in rows:
                print(
                    f"{row[0]:<{w_name}} | {row[1]:<{w_time}} | {row[2]:<{w_amount}} | {row[3]:<{w_type}}")
        print("")

        return all_schedules_clean

    # --- MAIN VIEW SCHEDULE LOGIC ---
    all_schedules = print_all_schedules()
    return all_schedules


# -- ADD SCHEDULE FUNCTION --
def add_schedule(time: str, amount: int | str, feeder_number: int) -> None:
    amount = str(amount)
    feeder_number = str(feeder_number)
    script_path = "./add_scheduled_feed.sh"

    # 1. Translate 'auto' amount
    if amount == "auto":
        amount = feeders_list[feeder_number]["default_amount"]

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


# -- REMOVE SCHEDULE FUNCTION --
def remove_schedule(time: str, feeder_number: int, clean_data: dict, all_schedules: dict) -> None:
    # NOTE Schedule format: (feeder_name: str, time: str, amount: str, source: str)

    # Validation
    feeder_id: int = get_id_by_number(clean_data, feeder_number)

    print(f"DEBUG  5 | {all_schedules=}")
    print(f"DUBUG  8 | {clean_data=}")
    matching_result_app = [item for item in all_schedules if item[0] == clean_data[feeder_id]['name'] and item[1]
                           == time and item[3] == "App"]
    print(f"DEBUG 10 | {matching_result_app=}")
    if matching_result_app:
        print(
            f"❌ Cannot remove schedule at {time} for Feeder #{feeder_number}.")
        print(f"Please remove it via the PetSafe SmartFeed app 📲.")
        return

    matching_result = [item for item in all_schedules if item[0] == clean_data[feeder_id]['name'] and item[1]
                       == time]
    print(f"DEBUG 12 | {matching_result=}")
    if not matching_result:
        print(
            f"❌ No schedule found at {time} for Feeder #{feeder_number}. Cannot remove.")
        return

    # TODO: handle duplicate schedules at same time?

    """
    Calls the remove_scheduled_feed.sh script to delete a specific cron job.
    Returns True if successful, False if the job wasn't found or an error occurred.
    """
    print(f"DEBUG 20 | {feeder_number=} {time=}")
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


# TODO: Create scheduled removal (cron job to trigger remove_scheduled_feed.sh in the future)

# --- MAIN INPUT FUNCTION ---
def task_input() -> None:
    action = input(
        "Select action: Add (A), Remove (R), View (V), Exit (X): ").strip().lower()

    # INPUT: ADD ACTION
    if action in ['add', 'a']:
        time = get_time()
        feeder_number = get_feeder_number_flex()
        amount = get_amount()
        if feeder_number == "all":
            add_schedule(time, amount, 1)
            add_schedule(time, amount, 2)
        else:
            add_schedule(time, amount, feeder_number)

    # INPUT: REMOVE ACTION
    elif action in ['remove', 'r', 'rm', 'd', 'del', 'delete']:
        # Print current schedules, for user reference
        print("Current schedules:")
        clean_data: dict = fetch_feeder_info()
        all_schedules: list[tuple] = view_schedule(clean_data)

        # Prompt for machine & time to remove
        feeder_number = get_feeder_number_flex()
        time = get_time()

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


# --- MAIN FUNCTION ---
def main():
    task_input()


# --- RUN MAIN FUNCTION ---
# TODO: change if it needs to consume command-line arguments?
if __name__ == "__main__":
    main()
