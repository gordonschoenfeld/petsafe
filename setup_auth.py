import json
import os
import petsafe_smartfeed as sf

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

filepath = "config/petsafe_tokens.json"
os.makedirs(os.path.dirname(filepath), exist_ok=True)
with open(filepath, "w") as f:
    json.dump(tokens, f, indent=4)
