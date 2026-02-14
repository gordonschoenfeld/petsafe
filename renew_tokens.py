#!/usr/bin/env python3
import json
import os
import petsafe_smartfeed as sf
import requests
import sys


# --- 1. SETUP PATHS ---
# calculate the absolute path to the folder where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, "tokens_petsafe.json")


# --- 2. DEFINE THE PATCH ---
def patched_refresh_tokens(self):
    """
    Patched method to handle missing RefreshToken in AWS response.
    Global fix for all scripts that import this module.
    """
    CLIENT_ID = "18hpp04puqmgf5nc6o474lcp2g"

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

    try:
        response = requests.post(
            "https://cognito-idp.us-east-1.amazonaws.com/",
            json=data,
            headers=headers
        ).json()
    except Exception as e:
        print(f"Warning: Connection to AWS failed: {e}")
        return

    if "AuthenticationResult" in response:
        self.id_token = response["AuthenticationResult"]["IdToken"]
        self.access_token = response["AuthenticationResult"]["AccessToken"]
        # The critical fix: use .get() to avoid crashing
        self.refresh_token = response["AuthenticationResult"].get(
            "RefreshToken", self.refresh_token)
    else:
        print(f"Warning: AWS refused token refresh. Response: {response}")


# --- 3. APPLY THE PATCH IMMEDIATELY ---
sf.PetSafeClient.refresh_tokens = patched_refresh_tokens


# --- 4. HELPER FUNCTION ---
def refresh_disk_tokens():
    """
    Loads tokens from disk, refreshes them via AWS, and saves them back.
    """
    # Uses the absolute path defined at the top
    try:
        with open(TOKEN_FILE, "r") as f:
            tokens = json.load(f)

        # Instantiate client (triggers the patched refresh if needed)
        client = sf.PetSafeClient(
            email=tokens["email"],
            id_token=tokens["id_token"],
            refresh_token=tokens["refresh_token"],
            access_token=tokens["access_token"]
        )

        new_tokens = {
            "email": tokens["email"],
            "id_token": client.id_token,
            "access_token": client.access_token,
            "refresh_token": client.refresh_token
        }

        with open(TOKEN_FILE, "w") as f:
            json.dump(new_tokens, f, indent=4)

        return client

    except FileNotFoundError:
        print(f"Error: {TOKEN_FILE} not found.")
        print("Please run setup_auth.py (and ensure it saves to the correct folder)!")
        sys.exit(1)
    except Exception as e:
        print(f"Error refreshing tokens: {e}")
        sys.exit(1)


# --- 5. EXECUTION BLOCK ---
if __name__ == "__main__":
    refresh_disk_tokens()
