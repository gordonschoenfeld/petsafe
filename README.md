# What this library does
If you have PetSafe feeders, this library enables you to
1. securely schedule feedings starting ***from*** a date to a date
1. securely schedule feedings for ***multiple feeders*** simultaneously (and with different amounts!)

It's really useful for trips: saving you from needing to remember to set a new scheduled feed when your trip starts, and then *again* you'll need to remember to cancel it. Well remember no more: with this library, you can pre-set a start and end date!

This code uses Techzune's PetSafe smartfeed library (https://github.com/Techzune/petsafe_smartfeed) to surface hooks to interact with the PetSafe API.


# Setup instructions
This setup should take 5–10 minutes.

## 1. Prerequisites

### Set up your PetSafe feeder(s) and app
If you haven't done so already, you should use the official PetSafe channels to set up your account on PetSafe, and connect your feeders to it.

### Upgrade to at least Python 3.6+
Ensure that your device's Python version is at least 3.6. 
* In terminal: `python3 --version`

If your Python version is below 3.6:
* Go to [python.org/downloads](https://www.python.org/downloads), and download and install the latest version of Python from there.

### pip is installed
!!!!!!TODO: install pip
`sudo python3 -m ensurepip --upgrade`


### (For Macs) Cron is explicitly enabled
Apple considers Cron deprecated, but still possible to enable. To enable it:
1. MacOS 'System Preferences' -> 'Security & Privacy' -> (menu-pick on left side) 'Full Disk Access' panel
1. Once there, locate the 'cron' program in the file-system using the Finder (must use the pull-down menu 'Go' -> 'Go to folder ...' feature to get to it
1. Drag and drop the 'cron' program (again, located at the system file-path of '/usr/sbin/cron') into the list of programs on the 'System Preferences' panel opened already
1. Make sure the little check-box is checked to enable to the program

### (Required for Shortcuts usage) Set up SSH into your server
See guide here: https://www.digitalocean.com/community/tutorials/how-to-use-ssh-to-connect-to-a-remote-server




## 2. Clone this repo to your machine
* Access the Unix-based device (e.g. Mac, Raspberry Pi) that these functions will run off of. SSH into it if necessary.
* In terminal:
```
cd <YOUR/PREFERRED/PARENT/FOLDER/PATH>
git clone https://github.com/gordonschoenfeld/petsafe
```
If asked, enter your github credentials.

## 3. Run wizard, to establish your connection and get a key from PetSafe

### Install connectivity library
* In terminal:
```
pip3 install petsafe-smartfeed --target /api
python3 setup/setup_wizard.py api/install
```

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
To use this program, **run in terminal: `python3 petsafe_main.py`**, then follow the prompts in the console. Or, if you've set up Shortcuts, you can also run the shortcut called "PetSafe" to get the same functionalities.

# Limitations
* Your have a Unix-based server. This includes Mac, Linux, and Raspberry Pi. Windows is not supported.
* Your server must be on and connected to the internet at feeding time.
  * This library works by setting Cron jobs on your computer. When one of these Cron jobs triggers, it sends a one-off request to "feed now". Therefore, if at the moment of the Cron job triggering (i.e. feeding time), if there is no connection, the feeding will not take place and will not try again that day. It will, however, try to trigger again the next day if possible.
  * Because of this, running this on an always-on server (e.g. Raspberry Pi) is strongly recommended.
* Feedings scheduled through this library cannot be seen or edited from the PetSafe app.
* Feedings scheduled through the PetSafe app cannot be edited from this library. (They can, however, be viewed).

# FAQ
## What OSs are supported, and why?
Unix-based OSs (including macOS, Linux, and Raspberry Pi) are supported. All scheduling functions are built in Crontab, which is Unix-specific.

## Is this secure?
It's more secure than your PetSafe app is:
* Scheduled feeding information is stored only on your server, then at feeding time, your server sends a one-off request to PetSafe directly to "feed now". No data goes to a 3rd party.
* Config files (with feeder names, feeding times, and SSH login data) live on your local machine, not on PetSafe's servers.

## What if I add/remove/rename feeders, or want to change the default amounts?
Run in terminal: `python3 setup_wizard.py`, then follow the prompts in the console. It will ask for your confirmation for overwriting the existing settings file. Or, you can directly edit `config/feeders_config.json`.

**WARNING**: Any changes to ID numbers for your devices will break existing scheduled tasks (current for future). I recommend that you first remove all tasks before making any changes to `config/feeders_config.json`, then re-add them.

## Can I use this program to interact with scheduled feeds that were set in the PetSafe app?
Unfortunately, no. Due to limitations in [Techzune's PetSafe smartfeed library](https://github.com/Techzune/petsafe_smartfeed), the app-scheduled feeds are readable, but not actually editable or overwritable.

As a workaround, this library includes app-scheduled feeds when viewing (for context), but produces user-friendly errors if the user tries to edit or remove one of them.

## Why aren't my scheduled feedings actually triggering?
See the Limitations section, above.

# Copyright
TODO
