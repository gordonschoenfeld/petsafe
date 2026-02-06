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
