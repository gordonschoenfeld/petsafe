#!/usr/bin/python3

import json
import petsafe_smartfeed as sf
import requests


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


sf.PetSafeClient.refresh_tokens = patched_refresh_tokens

if __name__ == "__main__":
    try:
        # 1. Load the OLD tokens
        with open("petsafe_tokens.json", "r") as f:
            tokens = json.load(f)

        # 2. Instantiate the client
        # This triggers the internal validation, which calls our PATCHED refresh_tokens()
        client = sf.PetSafeClient(
            email=tokens["email"],
            id_token=tokens["id_token"],
            refresh_token=tokens["refresh_token"],
            access_token=tokens["access_token"]
        )

        # 3. If we get here, the patch worked! Save the NEW tokens.
        new_tokens = {
            "email": tokens["email"],
            "id_token": client.id_token,
            "access_token": client.access_token,
            "refresh_token": client.refresh_token
        }

        with open("petsafe_tokens.json", "w") as f:
            json.dump(new_tokens, f, indent=4)

    except Exception as e:
        print(f"❌ renew_tokens.py script: Failed to refresh tokens: {e}")
        # We exit with error so feed_now.py knows something went wrong
        exit(1)
