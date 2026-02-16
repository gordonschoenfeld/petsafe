# What this library does
If you have PetSafe feeders, this library enables you to
1. schedule feedings starting ***from*** a date to a date
1. schedule feedings for ***multiple feeders*** simultaneously (and with different amounts!)

It's really useful for trips: saving you from needing to remember to set a new scheduled feed when your trip starts, and then *again* you'll need to remember to cancel it. Well remember no more: with this library, you can pre-set a start and end date!

This code uses Techzune's PetSafe smartfeed library (https://github.com/Techzune/petsafe_smartfeed) to surface hooks to interact with the PetSafe API.


# Setup instructions
## 1. Prerequisites

### Set up your PetSafe feeder(s) and app
If you haven't done so already, you should use the official PetSafe channels to set up your account on PetSafe, and connect your feeders to it.

### Upgrade to at least Python 3.6+
Ensure that your python version is at least 3.6. 
* In terminal: `python3 --version`

If your Python version is below 3.6:
* Go to [python.org/downloads](https://www.python.org/downloads), and download and install the latest version of Python from there.

## 2. Create directory for this library
* In terminal: 
```
mkdir petsafe
cd petsafe
```

## 3. Run wizard, to establish your connection and get a key from PetSafe
### Install connectivity library
* In terminal: `pip install petsafe-smartfeed --target /api`
* In terminal: `python3 setup.py api/install`

### Retrieve tokens and establish config settings file
* In terminal, run: `python3 setup_auth.py`, then follow the prompts in the console.

Example resulting `config/feeders_config.json` config file:
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

## 4. Ready!
To use the features, **run in terminal: `python3 petsafe_main.py`**, then follow the prompts in the console.

# FAQ
## What if I add/remove/rename feeders, or want to change ?
Run in terminal: `python3 setup_wizard.py`, then follow the prompts in the console. It will ask for your confirmation for overwriting the existing settings file.

# Copyright
TODO

# Limitations
TODO