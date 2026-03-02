<!-- 
# Copyright (c) 2026 Gordon Schoenfeld
# Licensed under the MIT License.
# See LICENSE file in the project root for full license information.
-->

# What this library does
If you have PetSafe feeders, this library enables you to
1. securely schedule feedings starting ***from*** a date ***to*** a date
1. securely schedule & cancel feedings for ***multiple feeders*** simultaneously (and with different amounts!)

This is especially useful for trips: you currently need to remember to schedule feedings when your trip starts, and then *again* you'll need to remember to cancel it. Well remember no more: with this library, you can pre-set start & end dates whenever!



# Setup instructions (~5 mins)

## 0. Prerequisites

### Set up your PetSafe feeder(s) and app
Use the official PetSafe channels to set up your account on PetSafe, and connect your feeders to it.

### Upgrade to at least Python 3.6+
Ensure that your device's Python version is at least 3.6. 
* In terminal: `python3 --version`

If your Python version is below 3.6:
* Go to [python.org/downloads](https://www.python.org/downloads), and download and install the latest version of Python from there.

### Install Pip
If pip is not already installed on your system, install it.
* In terminal: `sudo python3 -m ensurepip --upgrade`

### (For Macs) Cron explicitly enabled
Apple considers Cron deprecated, but still possible to enable. To enable it:
1. MacOS 'System Preferences' -> 'Security & Privacy' -> (menu-pick on left side) 'Full Disk Access' panel
1. Once there, locate the 'cron' program in the file-system using the Finder (use the pull-down menu 'Go' -> 'Go to folder ...' feature to get to it)
1. Drag and drop the 'cron' program (again, located at the system file-path of '/usr/sbin/cron') into the list of programs on the 'System Preferences' panel opened already
1. Make sure the toggle is checked to enable to the program

### (Required for Shortcuts usage) SSH into your server is set up
See guide here: https://www.digitalocean.com/community/tutorials/how-to-use-ssh-to-connect-to-a-remote-server




## 1. Clone this repo to your machine
* Access the Unix-based device (e.g. Mac, Raspberry Pi) that these functions will run off of. SSH into it if necessary.
* In terminal:
```
cd <YOUR/PREFERRED/PARENT/FOLDER/PATH>
git clone https://github.com/gordonschoenfeld/petsafe
```
If asked, enter your github credentials.


## 2. Run setup wizard

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


## 3. (If using Apple Shortcuts) Initialize Shortcuts app (one-time)
* Grant app permissions to run scripts
  * (On Mac) Shortcuts > Settings > Advanced > Allow Running Scripts
  * (On iOS) iOS Settings app > Apps > Shortcuts > Advanced > Allow Running Scripts

* Add SSH credentials in the Shortcuts App
  * Open the Shortcuts app and edit the main 'PetSafe' shortcut
  * Scroll down to each 'Run script over SSH' action
  * 🔐 We do not ask for your password or SSH key in this script so it stays securely on your device
  * Expand the action and under 'Authentication', choose 'SSH Key' or 'Password'
    * If you use a password to SSH into your device:
      * In each black-and-white 'Run Scripts Over SSH' module in shortcuts, change Authentication to 'Password':
        * 1 instance: "PetSafe View" shortcut
        * 4 instance: "PetSafe Remove" shortcut
        * 8 instances: "PetSafe Add" shortcut
      * Enter your password directly into the new Password field.
    * If you use an SSH key:
      * Click on the Authentication field and change it from "Password" to SSH Key.
      * A new row will appear below it, typically labeled something like SSH Key: ed25519 Key (or RSA). Click on that key label.
      * A menu will pop up. Click Copy Public Key. (Note: Never share or copy the Private Key. You only need the Public Key for the server).
      * SSH into your device, if applicable.
      * In terminal: `mkdir -p ~/.ssh ; touch ~/.ssh/authorized_keys ; nano ~/.ssh/authorized_keys`
    * Paste the public key you copied from Shortcuts on a new line. It should look like a single, long string starting with ssh-ed25519 or ssh-rsa.
    * Save and exit (COMMAND+O, Enter, COMMAND+X).
    * Lock down file permissions. In terminal: `chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys`
* Grant first-run shortcut permissions
  * The first time you run each shortcut, you will be asked for permission to run other shortcuts. When you get a prompt like: *Allow "PetSafe XYZ" to run another shortcut?* ==> click Allow.
  * The first time you run certain scenarios, you will be asked for permission for the app to read from your SSH config file to make SSH calls. When you get a prompt like *Allow "PetSafe XYZ" to use 1 text item in an SSH script on URL/IP?* ==> click Always Allow.



## Ready!
To use this program, **run in terminal: `python3 petsafe_main.py`**, then follow the prompts in the console. Or, if you've set up Shortcuts, you can also run the shortcut called "PetSafe" to get the same functionalities.




# Limitations
* Your have a Unix-based server. This includes Mac, Linux, and Raspberry Pi. Windows is not supported.
* Your server must be on and connected to the internet at feeding time.
  * This library works by setting Cron jobs on your computer. When one of these Cron jobs triggers, it sends a one-off request to "feed now". Therefore, if at the moment of the Cron job triggering (i.e. feeding time), if there is no connection, the feeding will not take place and will not try again that day. It will, however, try to trigger again the next day if possible.
  * Because of this, running this on an always-on server (e.g. Raspberry Pi) is strongly recommended.
* Feedings scheduled through this library cannot be seen or edited from the PetSafe app.
* Feedings scheduled through the PetSafe app cannot be edited from this library. (They can, however, be viewed).




# FAQ
## A. What OSs are supported? Why not Windows?
Unix-based OSs (including macOS, Linux, and Raspberry Pi) are supported. All scheduling functions are built in Crontab, which is Unix-specific.

## B. Is this secure?
It's more secure than your PetSafe app is:
* Scheduled feeding information is stored only on your server, then at feeding time, your server sends a one-off request to PetSafe directly to "feed now". No data goes to a 3rd party.
* Config files (with feeder names, feeding times, and SSH login data) live on your local machine, not on PetSafe's servers.

## C. What if I add/remove/rename feeders, or want to change the default amounts?
Run in terminal: `python3 setup_wizard.py`, then follow the prompts in the console. It will ask for your confirmation for overwriting the existing settings file. Or, you can directly edit `config/feeders_config.json`.

**WARNING**: Any changes to ID numbers for your devices will break existing scheduled tasks (current for future). I recommend that you first remove all tasks before making any changes to `config/feeders_config.json`, then re-add them.

## D. Can I use this program to interact with scheduled feeds that were set in the PetSafe app?
Unfortunately, no. Due to limitations in [Techzune's PetSafe smartfeed library](https://github.com/Techzune/petsafe_smartfeed), the app-scheduled feeds are readable, but not actually editable or overwritable.

As a workaround, this library includes app-scheduled feeds when viewing (for context), but produces user-friendly errors if the user tries to edit or remove one of them.

## E. Why aren't my scheduled feedings actually triggering?
See the Limitations section, above.




# Copyright
Copyright (c) 2026 Gordon Schoenfeld

Licensed under the MIT License. See LICENSE file in the project root for full license information.