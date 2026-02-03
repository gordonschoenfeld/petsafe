#!/usr/bin/env python3

import sys
import json
import petsafe_smartfeed as sf

# --- AUTH SETUP ---
try:
    with open("/Users/gordonschoenfeld/Python/PetSafe/petsafe_tokens.json", "r") as f:
        saved_tokens = json.load(f)
except FileNotFoundError:
    print("Error: Tokens file not found.")
    exit()

client = sf.PetSafeClient(
    email=saved_tokens["email"],
    id_token=saved_tokens["id_token"],
    refresh_token=saved_tokens["refresh_token"],
    access_token=saved_tokens["access_token"]
)

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


headers = {
    'Content-Type': 'application/json',
    'Authorization': client.id_token
}

# -- END AUTH SETUP --
with open("feeders_list.json", "r") as f:
    feeders_list = json.load(f)

feeders = client.feeders

if __name__ == "__main__":
    # 1. Check if the correct number of arguments were passed
    # sys.argv[0] is the script name, [1] is feeder_number, [2] is amount
    if len(sys.argv) < 3:
        print("Error: Missing arguments. Usage: python script.py <feeder_index> <amount>")
        sys.exit(1)

    try:
        # 2. Parse arguments
        feeder_id = feeders_list[sys.argv[1]]["id"]
        feed_amount = int(sys.argv[2])

        # 3. Validate that the feeder index actually exists
        if feeder_id not in [feeder.id for feeder in feeders]:
            print(
                f"Error: Feeder ID {feeder_id} is not recognized.")
            sys.exit(1)

        # 4. Execute the logic
        print(f"Triggering Feeder #{feeder_id} for amount: {feed_amount}")
        feeder_id.feed(amount=feed_amount, slow_feed=False)

    except ValueError:
        print("Error: Feeder number and Amount must be integers.")
        sys.exit(1)

# input format:   python3 feed_now.py <feeder_index> <amount>
# input example:  python3 feed_now.py 2 4
