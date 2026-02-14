#!/usr/bin/python3

# ABOUT
# This script initially establishes auth from PetSafe, for interaction with their API.
# It writes them into config/petsafe_tokens.json.

import json
import os
import petsafe_smartfeed as sf

# -- Print headers --
width = 36
message = "BEGINNING AUTH SETUP"
print(f"")
print(f"=" * width)
print(f"|" + message.center(width-2) + "|")
print(f"." * width)

# 1. Define email
email: str = input("Your email address associated with PetSafe: ")

# 2. Initialize client and request a code
print(f"Requesting access code for {email}...")
client = sf.PetSafeClient(email=email)
client.request_code()

# 3. User inputs the code received in email
code = input("Enter the code sent to your email: ")

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
filename = "petsafe_tokens.json"
os.makedirs(os.path.dirname(file_dir + filename), exist_ok=True)
with open(file_dir + filename, "w") as f:
    json.dump(tokens, f, indent=4)

print(
    f"✅ Success: {file_dir + filename} has been created with your auth tokens.")

# -- Print footers --
width = 36
message = "COMPLETED AUTH SETUP"
print(f"." * width)
print(f"|" + message.center(width-2) + "|")
print(f"=" * width)
print(f"")
