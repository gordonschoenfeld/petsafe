import petsafe_smartfeed as sf
import json


# -- Get tokens --
with open("tokens_petsafe.json", "r") as file:
    token = json.load(file)


# -- Fetch feeders data --
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

# -- Parse feeder info --
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


# -- Print feeders before inputs --
for feeder in feeders_map:
    print(f"• Friendly device number: {feeder}")
    print(f"  ├─Name: {feeders_map[feeder]['name']}")
    print(f"  ├─API ID: {feeders_map[feeder]['api_id']}")
    print(f"  └─ID: {feeders_map[feeder]['id']}")
print()


# -- Set new device numbers --
device_num_map: dict[str: str] = {}


def assign_default_amount(feeder):
    new_default_amount = input(
        f"  - Enter new default feed amount, in ⅛-cup units: ").strip()
    # Case: escape
    if new_default_amount in ["x", "exit"]:
        print(f"Exiting program.")
        exit()
    # Case: bad input ==> go back
    elif not new_default_amount.isnumeric() or not int(new_default_amount) in range(1, 9):
        print(f"    ⚠️ Error: You must assign an integer value, 1 ~ 8 (e.g. 2 = ¼ cup).")
        return assign_default_amount(feeder)
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


def input_device_nums_action(feeders_map):
    # Get new name & default amount for each feeder
    for feeder in feeders_map:
        # Get and add new default amount
        print(
            f"• Please initialize settings for device: {feeders_map[feeder]['name'].upper()}")
        default_amount = assign_default_amount(feeder)
        feeders_map[feeder]["default_amount"] = default_amount
        # Get new device_num
        input_one_device_number(feeder)

    # Iterate through mapping of Old Key -> New Key, transfer over to new_feeders_map
    new_feeders_map = {}

    for old_key, new_key in device_num_map.items():
        new_feeders_map[new_key] = feeders_map[old_key]
    feeders_map = new_feeders_map

    return new_feeders_map


# Overwrite feeders_map with new labels
feeders_map = input_device_nums_action(feeders_map)


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
