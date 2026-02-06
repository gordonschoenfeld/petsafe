#!/usr/bin/env python3

# Input format:   python3 feed_now.py <feeder_number> <amount>
# Input example:  python3 feed_now.py 1 1

import sys
import json
import petsafe_smartfeed as sf
import subprocess

# --- AUTH SETUP ---
try:
    with open("petsafe_tokens.json", "r") as f:
        saved_tokens = json.load(f)
except FileNotFoundError:
    print("Error: Tokens file not found.")
    exit()

# --- RENEW TOKENS ---
subprocess.run(["python3", "renew_tokens.py"])

# --- INSTANTIATE CLIENT ---
client = sf.PetSafeClient(
    email=saved_tokens["email"],
    id_token=saved_tokens["id_token"],
    refresh_token=saved_tokens["refresh_token"],
    access_token=saved_tokens["access_token"]
)

# --- TOKEN REFRESH LOGIC ---
print("\n--- FORCING TOKEN REFRESH ---")
try:
    # 1. Force the client to get a new token from AWS right now
    client.refresh_tokens()

    # 2. Update your headers with the NEW token
    # Note: We strip any whitespace just in case
    fresh_token = client.id_token.strip()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': fresh_token
    }

    print("✅ Token Refreshed.")
    # Debug: Print the last 10 chars to verify it changed
    print(f"Token ends in: ...{fresh_token[-10:]}")
except Exception as e:
    print(f"❌ Refresh Failed: {e}")
    exit()
# --- END TOKEN REFRESH LOGIC ---


headers = {
    'Content-Type': 'application/json',
    'Authorization': client.id_token
}

# -- END AUTH SETUP --
with open("feeders_general_info.json", "r") as f:
    feeders_list = json.load(f)

feeders: list[object] = client.feeders

if __name__ == "__main__":
    # 1. Check if the correct number of arguments were passed
    # sys.argv[0] is the script name, [1] is feeder_number, [2] is amount
    if len(sys.argv) < 3:
        print("Error: Missing arguments. Usage: python script.py <feeder_index> <amount>")
        sys.exit(1)

    try:
        # 2. Parse arguments
        feeder_number: str = sys.argv[1]
        feeder_name: str = feeders_list[feeder_number]["name"]
        feeder_id: int = feeders_list[feeder_number]["id"]
        feed_units: int = int(sys.argv[2])
        cups_per_unit = {1: "1/8 cup", 2: "1/4 cup", 3: "3/8 cup", 4: "1/2 cup",
                         5: "5/8 cup", 6: "3/4 cup", 7: "7/8 cup", 8: "1 cup"}
        feed_amount: str = cups_per_unit.get(
            feed_units, f"Invalid amount ({feed_units})")
        target_feeder: int = int(feeder_number) - 1

        # look up index for the feeder_id within feeders
        feeder_index = None
        for index, feeder in enumerate(feeders):
            if feeder.id == feeder_id:
                feeder_index = index
                break

        # 3. Validate that the feeder index actually exists
        if feeder_id not in [feeder.id for feeder in feeders]:
            print(
                f"Error: Feeder {feeder_number} (ID: {feeder_id}) is not recognized.")
            sys.exit(1)

        # 4. Execute the logic
        print(
            f"Requesting Feeder: {feeder_name} to feed amount: {feed_amount}...")
        feeders[target_feeder].feed(amount=feed_units, slow_feed=False)

    except ValueError:
        print("Error: Feeder number must be a string, and Amount an integer.")
        sys.exit(1)
