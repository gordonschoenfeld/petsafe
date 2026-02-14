# What this library does
For users of PetSafe feeders, this library enables you to **schedule feedings starting *from* a date *to* a date**. It's really useful for trips: saving you from needing to remember to set a new scheduled feed when your trip starts, and then *again* you'll need to remember to cancel it. Well remember no more: with this library, you can pre-set a start and end date!

This code uses Techzune's PetSafe smartfeed library (https://github.com/Techzune/petsafe_smartfeed) to surface hooks to interact with the PetSafe API.


# Setup instructions
## 1. Set up your PetSafe feeder(s) and app
If you haven't done so already, you should use the official PetSafe channels to set up your account on PetSafe, and connect your feeders to it.

## 2. Create a directory for this library
* In terminal: 
```
mkdir petsafe
cd petsafe
```

## 3. Establish your connection and get a key from PetSafe
### Install connectivity library
* In terminal: `pip install petsafe-smartfeed`
* In terminal: `python3 setup.py install`

### Retrieve tokens
TODO: would `auth_setup.py` work here instead????

#### Option A. Get tokens using command line
 * Execute `python -m petsafe_smartfeed [email@example.com]` to request an email code.
 * Check your email for an email code from PetSafe.
 * Enter your code to generate tokens.

#### Option B. Get tokens using Python
```
import petsafe_smartfeed as sf

# replace with your email address
client = sf.PetSafeClient(email="email@example.com")
client.request_code()

# check your email for a code
code = input("Enter email code: ")
token = client.request_tokens_from_code(code)

print("email:", client.email)
print("id_token:", client.id_token)
print("refresh_token:", client.refresh_token)
print("access_token:", client.access_token)
```

### Save PetSafe login tokens
In terminal, run: `python3 renew_tokens.py`. It will save (or update) your tokens in a file called `tokens_petsafe.json`. 


## 3. Establish your `feeders_general_info.json` file
In terminal, run `python3 setup_wizard.py`. It will guide you through the config of your feeders and your their default feeding amounts.

Example resulting `feeders_general_info.json` file:
```
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
```

# FAQ
## What if I add/remove/rename feeders?
Delete your `feeders_general_info.json` file, and rerun in terminal: `python3 setup_wizard.py`.

# Copyright
TODO

# Limitations
TODO