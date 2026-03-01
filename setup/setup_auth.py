#!/usr/bin/python3

# Copyright (c) 2026 Gordon Schoenfeld
# Licensed under the MIT License.
# See LICENSE file in the project root for full license information.

# ABOUT
# This script establishes auth from PetSafe, for interaction with their API.
# It writes them into /config/tokens_petsafe.json.

import json
import os
import petsafe_smartfeed as sf

# -- Print headers --
width = 36
message = "AUTH SETUP: STARTING"
print(f"")
print(f"=" * width)
print(f"|" + message.center(width-2) + "|")
print(f"." * width)

# 0. Explain module
print(f"ℹ️ Establishing authorization from PetSafe, for interaction with their API.")
print(f"ℹ️ It writes them into /config/tokens_petsafe.json.")
print(f"")

# 1. Define email
email: str = input("Your email address associated with PetSafe: ").strip()
# escape hatch
if email.lower() in ["x", "exit", "q", "quit"]:
    print(f"Exiting program.")
    exit()

# 2. Initialize client and request a code
print(f"Requesting access code for {email}...")
client = sf.PetSafeClient(email=email)
client.request_code()

# 3. User inputs the code received in email
code = input("Enter the code sent to your email: ").strip()

# 4. Exchange code for tokens
client.request_tokens_from_code(code=code)

# 5. Save the tokens to a file
tokens = {
    "email": email,
    "id_token": client.id_token,
    "refresh_token": client.refresh_token,
    "access_token": client.access_token
}

file_dir = "config/"
filename = "tokens_petsafe.json"
os.makedirs(os.path.dirname(file_dir + filename), exist_ok=True)
with open(file_dir + filename, "w") as f:
    json.dump(tokens, f, indent=4)

print(
    f"✅ Success: {file_dir + filename} has been created with your auth tokens.")

# -- Print footers --
width = 36
message = "AUTH SETUP: COMPLETE"
print(f"." * width)
print(f"|" + message.center(width-2) + "|")
print(f"=" * width)
print(f"")
