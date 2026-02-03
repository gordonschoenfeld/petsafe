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


# GET FEEDER INFO & CLEAN UP DATA
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


def get_feeder_number_flex() -> int:
    feeder_number = input(
        "Enter feeder number to add schedule to: [1 Under ***REMOVED***, 2 ***REMOVED***, 3 both]: ").strip()
    # reject invalid feeder number
    if feeder_number not in ['1', '2', '3']:
        print("Invalid feeder number. Please enter 1, 2, or 3.")
        return get_feeder_number_flex()  # Retry
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
    if amount in ['auto', 'AUTO', 'Auto', 'a', 'A']:
        return "auto"
    else:
        return int(amount)


# -- VIEW SCHEDULE FUNCTION --
def view_schedule(clean_data) -> None:

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
            amount = parts[-1]
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
                    (feeder['name'], schedule['time'], schedule['amount'], "App"))
        return system_schedules

    # --- PRINT ALL SCHEDULES ---
    def print_all_schedules():
        # Get lists from both sources and combine both lists
        # Output format: (feeder_name, time, amount, source)
        cron_schedules = get_cron_schedules()
        system_schedules = get_system_schedules()
        all_schedules = cron_schedules + system_schedules

        # Convert amount from units to cups for display
        cups_per_unit = {1: "1/8 cup", 2: "1/4 cup", 3: "3/8 cup", 4: "1/2 cup",
                         5: "5/8 cup", 6: "3/4 cup", 7: "7/8 cup", 8: "1 cup"}
        for i in range(len(all_schedules)):
            feeder_name, time, amount, source = all_schedules[i]
            if amount.isdigit():
                amount_units = int(amount)
                amount_str = cups_per_unit.get(amount_units)
            else:
                amount_str = "AUTO"
            all_schedules[i] = (feeder_name, time, amount_str, source)

        # --- PRINT TABLE ---
        # Define column widths
        w_name, w_time, w_amount, w_type = 20, 7, 8, 10

        # Print Header
        print(f"{'Feeder Name':<{w_name}} | {'Time':<{w_time}} | {'Amount':<{w_amount}} | {'Note':<{w_type}}")
        print("-" * (w_name + w_time + w_amount + w_type + 9))

        if not all_schedules:
            print("No feeder schedules found.")
        else:
            # Sort by Time (HH:MM)
            rows = sorted(all_schedules, key=lambda x: (x[0], x[1]))
            for row in rows:
                print(
                    f"{row[0]:<{w_name}} | {row[1]:<{w_time}} | {row[2]:<{w_amount}} | {row[3]:<{w_type}}")

    # --- MAIN VIEW SCHEDULE LOGIC ---
    print_all_schedules()


# --- MAIN INPUT FUNCTION ---
def task_input() -> None:
    action = input(
        "Select action: Add (A), Remove (R), View (V), Exit (X): ").strip().lower()

    # INPUT: ADD ACTION
    if action in ['add', 'a']:
        time = get_time()
        feeder_number = get_feeder_number_flex()
        amount = get_amount()
        if feeder_number == 3:
            add_schedule(time, amount, 1)
            add_schedule(time, amount, 2)
        else:
            add_schedule(time, amount, feeder_number)

    # INPUT: REMOVE ACTION
    elif action in ['remove', 'r', 'rm', 'd', 'del', 'delete']:
        # Print current schedules, for user reference
        print("Current schedules:")
        clean_data = fetch_feeder_info()
        view_schedule(clean_data)

        # Prompt for machine & time to remove
        feeder_number = get_feeder_number_flex()
        time = get_time()

        # Call remove function. Validation is handled inside function.
        if feeder_number == 3:
            remove_schedule(time, 1)
            remove_schedule(time, 2)
        else:
            remove_schedule(time, feeder_number)

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


# -- ADD SCHEDULE FUNCTIONS --
def add_schedule(time, amount, feeder_number) -> None:
    schedule_time = time
    feeder_id = feeder_number
    amount = amount
    script_path = "./set_schedule.sh"

    # 1. Translate 'auto' amount
    if amount == "auto":
        amount = feeders_list[str(feeder_id)]["default_amount"]

    try:
        # 2. Call the script with the arguments
        # The arguments are passed as a list: [Script, Arg1, Arg2, Arg3]
        result = subprocess.run(
            [script_path, schedule_time, str(feeder_id), str(amount)],
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
def remove_schedule(time, feeder_number) -> None:
    # The name of the script we are looking for in the cron list
    target_script = "feed_now.py"

    # TODO: special check and reject if it's an app side schedule (not cron)
    # TODO: validate time exists in cron for that feeder
    # TODO: translate feeder_number to feeder_id

    script_path = "./delete_schedule.sh"

    print(
        f"Removing schedule at {time} from Feeder #{feeder_number}... (Functionality not yet implemented)")


# --- MAIN FUNCTION ---
def main():
    task_input()


# --- RUN MAIN FUNCTION ---
# TODO: change if it needs to consume command-line arguments?
if __name__ == "__main__":
    main()
