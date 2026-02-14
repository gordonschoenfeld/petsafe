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


# -- Print feeders --
def print_all():
    for feeder in feeders_map:
        print(f"• Friendly device number: {feeder}")
        print(f"  ├─Name: {feeders_map[feeder]['name']}")
        print(f"  ├─API ID: {feeders_map[feeder]['api_id']}")
        print(f"  └─ID: {feeders_map[feeder]['id']}")
    print()


print_all()


# -- Set new device numbers --
device_num_map: dict[str: str] = {}


def input_one_device_number(feeder):
    new_device_number = input(
        f"Enter new friendly device number (e.g. 1) for {feeder} ('{feeders_map[feeder]['name']}'): ").strip()
    if not new_device_number.isdigit():
        print(f"Error: only give a number")
        return input_one_device_number(feeder)
    else:
        device_num_map[feeder] = new_device_number
        print(f"DEBUG | {device_num_map=}")
        if new_device_number in device_num_map.values():
            print(f"This ID was already used.")
            redo_response = input(
                f"(A) Redo this one, or (B) Start from beginning of devices?: ").strip().lower()
            if redo_response == "a":
                return input_one_device_number(feeder)
            elif redo_response == "b":
                device_num_map = {}
                return input_device_nums_action()
            else:
                print(f"Response not understood. Starting over.")
                device_num_map = {}
                return input_device_nums_action()
        else:
            return new_device_number


def input_device_nums_action():
    for feeder in feeders_map:
        new_number = input_one_device_number(feeder)
        print(f"DEBUG | {feeder=}")
        print(f"DEBUG | {new_number=}")
        feeder = new_number


input_device_nums_action()

print_all()
