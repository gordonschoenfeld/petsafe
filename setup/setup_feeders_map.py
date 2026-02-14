#!/usr/bin/python3

# ABOUT
# This script establishes a simple json config of feeders, names and user preferences.
# They will be written into /config/feeders_general_info.json.

import json
import os
import petsafe_smartfeed as sf
import sys

# -- Establish vars --
file_dir = "config/"
filename_feeders_info = "feeders_general_info.json"
filename_tokens = "tokens_petsafe.json"


# -- Check if file already exists --
def check_file_exists(filename: str) -> bool:
    if os.path.exists(filename):
        return True
    else:
        return False


# -- Fetch tokens --
def fetch_tokens_from_file():
    if not check_file_exists(file_dir + filename_tokens):
        print(
            f"⚠️ Error: The file '{file_dir + filename_tokens}' does not exist.")
        print(f"Please run setup_auth.py (and ensure it saves into /config)!")
        print(f"Exiting now.")
        sys.exit()
    else:
        with open(file_dir + filename_tokens, "r") as file:
            token = json.load(file)
            return token


# -- Fetch feeders data --
def fetch_feeders_data(token: dict):
    '''
    Sample raw data:
    {
        "1": {
            "id": 12345,
            "api_id": "m-1A2345B6789C",
            "default_amount": 2,
            "name": "Living Room"
        },
        "2": {
            "id": 123456,
            "api_id": "m-9F8C39023AE4",
            "default_amount": 3,
            "name": "Kitchen"
        }
    }
    '''

    print(f"Fetching feeders data (this may take up to 30 seconds)...")

    client = sf.PetSafeClient(token["email"],
                              token["id_token"],
                              token["refresh_token"],
                              token["access_token"])
    feeders = client.feeders

    print(f"Successfully fetched feeders data. List:")
    print()
    return feeders


# -- Parse feeder info --
def parse_feeder_info(feeders: dict[dict]):
    feeders_map = {}
    i = 1

    for feeder in feeders:
        temp_name = "TEMP" + str(i)
        feeders_map[temp_name] = {}
        feeders_map[temp_name]["id"] = feeder.id
        feeders_map[temp_name]["api_id"] = feeder.data["thing_name"]
        feeders_map[temp_name]["name"] = feeder.data["settings"]["friendly_name"]
        feeders_map[temp_name]["default_amount"] = 1
        i += 1
    return feeders_map


# -- Set new device numbers --
device_num_map: dict[str: str] = {}


# -- Get inputs and rewrite dict --
def input_device_nums_action(feeders_map: dict):
    def input_default_amount(feeder):
        new_default_amount = input(
            f"  - Enter new default feed amount, in ⅛-cup units: ").strip()
        # Case: escape
        if new_default_amount in ["x", "exit"]:
            print(f"Exiting program.")
            exit()
        # Case: bad input ==> go back
        elif not new_default_amount.isnumeric() or not int(new_default_amount) in range(1, 9):
            print(
                f"    ⚠️ Error: You must assign an integer value, 1 ~ 8 (e.g. 2 = ¼ cup).")
            return input_default_amount(feeder)
        # Case: successful entry ==> continue
        else:
            cups_per_unit = {1: "⅛ cup", 2: "¼ cup", 3: "⅜ cup", 4: "½ cup",
                             5: "⅝ cup", 6: "¾ cup", 7: "⅞ cup", 8: "1 cup"}
            print(
                f"    ✅ Successfully set to {new_default_amount} unit(s) (= {cups_per_unit[int(new_default_amount)]})")
            return new_default_amount

    def input_one_device_number(feeder):
        new_device_number = input(
            f"  - Enter new friendly device number (e.g. 1): ").strip()
        # Case: bad input ==> go back
        if not new_device_number.isdigit():
            print(f"    ⚠️ Error: You must assign an integer value (e.g. 1).")
            return input_one_device_number(feeder)
        # Case: dupe value ==> go back
        elif new_device_number in device_num_map.values():
            print(f"    ⚠️ Error: This ID was already used.")
            redo_response = input(
                f"    (A) Reassign this one, (B) Start from beginning of devices, or (X) Exit: ").strip().lower()
            if redo_response == "a":
                return input_one_device_number(feeder)
            elif redo_response == "b":
                print(f"Starting over.")
                device_num_map.clear()
                return input_device_nums_action(feeders_map)
            elif redo_response in ["x", "exit"]:
                print(f"Exiting program.")
                exit()
            else:
                print(f"    ⚠️ Error: Response not understood. Starting over.")
                return input_device_nums_action()
        # Case: successful entry ==> continue
        else:
            print(f"    ✅ Successfully set ID to {new_device_number}")
            device_num_map[feeder] = new_device_number
            return new_device_number

    # TODO: Add action to optionally change name (recommended 6 chars or fewer)

    # Get new ID, name, & default amount for each feeder
    for feeder in feeders_map:
        # Get and add new default amount
        print(
            f"• Please initialize settings for device: {feeders_map[feeder]['name'].upper()}")
        default_amount = input_default_amount(feeder)
        feeders_map[feeder]["default_amount"] = default_amount
        # Get new device_num
        input_one_device_number(feeder)

    # Iterate through mapping of Old Key -> New Key, transfer over to new_feeders_map
    new_feeders_map = {}

    for old_key, new_key in device_num_map.items():
        new_feeders_map[new_key] = feeders_map[old_key]
    feeders_map = new_feeders_map

    return new_feeders_map


# -- Write to feeders info file --
def write_to_file(feeders_map: dict, filename: str = filename_feeders_info):
    # 'w' mode overwrites the file if it exists, or creates it if it doesn't
    with open(file_dir + filename, 'w', encoding='utf-8') as f:
        json.dump(feeders_map, f, indent=4, ensure_ascii=False)


# -- Main script --
def main():
    # -- Print headers --
    width = 36
    message = "TOKENS SETUP: STARTING"
    print(f"")
    print(f"=" * width)
    print(f"|" + message.center(width-2) + "|")
    print(f"." * width)

    # -- Get tokens --
    token: dict = fetch_tokens_from_file()

    # -- Fetch feeders data --
    feeders: dict[dict] = fetch_feeders_data(token)
    feeders_map: dict[dict] = parse_feeder_info(feeders)

    # -- Check if feeders file already exists. If exists, prompt: overwrite or abort? --
    feeders_info_file_existence: bool = check_file_exists(
        file_dir + filename_feeders_info)
    if feeders_info_file_existence:
        print(
            f"⚠️ Error: The file '{file_dir + filename_feeders_info}' already exists.")
        continue_overwrite: str = input(
            "Continue with overwrite? Y/N: ").strip().lower()
        if continue_overwrite in ["no", "n", "exit", "x", "quit", "q"]:
            print(f"Aborting feeders setup.")
            sys.exit()
        else:
            print(f"Continuing with overwrite.")

    # -- Print feeders before inputs --
    for feeder in feeders_map:
        print(f"• Friendly device number: {feeder}")
        print(f"  ├─Name: {feeders_map[feeder]['name']}")
        print(f"  ├─API ID: {feeders_map[feeder]['api_id']}")
        print(f"  └─ID: {feeders_map[feeder]['id']}")
    print()

    # -- Overwrite feeders_map with new labels --
    feeders_map: dict[dict] = input_device_nums_action(feeders_map)

    # -- Print feeders after inputs --
    print(f"Initialized feeders:")
    print()
    for feeder in feeders_map:
        print(f"• Friendly device number: {feeder}")
        print(f"  ├─Name: {feeders_map[feeder]['name']}")
        print(f"  ├─API ID: {feeders_map[feeder]['api_id']}")
        print(f"  ├─ID: {feeders_map[feeder]['id']}")
        print(f"  └─Default amount: {feeders_map[feeder]['default_amount']}")
    print()

    write_to_file(feeders_map)
    print(
        f"✅ Success: {file_dir + filename_feeders_info} has been created with your feeders config.")

    # -- Print footers --
    width = 36
    message = "TOKENS SETUP: COMPLETE"
    print(f"-" * width)
    print(f"|" + message.center(width-2) + "|")
    print(f"=" * width)
    print(f"")


if __name__ == "__main__":
    main()
