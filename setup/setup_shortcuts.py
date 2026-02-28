#!/usr/bin/python3

import itertools
import json
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


# Establish animation
fetch_done = False


def animate():
    # itertools.cycle loops through these characters forever
    for char in itertools.cycle(['|', '/', '-', '\\']):
        if fetch_done:
            break
        # \r moves the cursor back to the start of the line
        sys.stdout.write(f'\rRequesting 6 installations... {char} ')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write(f'\rRequest pop-ups generated!      \n')


# -- Print headers --
width = 36
message = "APPLE SHORTCUTS SETUP: STARTING"
print(f"")
print(f"=" * width)
print(f"|" + message.center(width-2) + "|")
print(f"." * width)

# -- PROMPT TO PROCEED OR SKIP --
print(f"ℹ️ If you want, you can also install easy UI and Siri capabilities via Apple Shortcuts.")

opt = input(
    f"  - Proceed with setting up Apple Shortcuts? Y/N: ").strip().lower()
# Case: opt out
if opt in ["x", "exit", "n", "no", "quit", "q"]:
    print(f"Opting out of Apple Shortcuts setup.")
    # -- Print footers --
    width = 36
    message = "APPLE SHORTCUTS SETUP: CANCELED"
    print(f"." * width)
    print(f"|" + message.center(width-2) + "|")
    print(f"=" * width)
    print(f"")
    exit()


# -- INTRO TEXT, PAUSE BEFORE INSTALL --
print(f"Installing Shortcuts from iCloud.")
print(f"You will be presented with 6 (six) pop-ups.")
print(f"For each one, click the pop-up's \"Add Shortcut\" button.")
input(f"Press RETURN/ENTER to continue.")

# Show install requests dialog (animated)
t = threading.Thread(target=animate)
t.start()

try:
    # Run installs
    shortcut_links = [
        "https://www.icloud.com/shortcuts/0cf5f0c06f6d4f7f8e8d59c2fd705e0a",    # PetSafe main
        "https://www.icloud.com/shortcuts/5fe0d58baaf1432d870a2438e8bbca27",    # Add
        "https://www.icloud.com/shortcuts/cdf087d017884c0c9aafea22fbb42bae",    # Remove
        "https://www.icloud.com/shortcuts/3b83f601cf54496dab14d93579ae4eb3",    # View
        "***REDACTED***",    # Remove Matches
        "https://www.icloud.com/shortcuts/fe111f50a001470d822d94096520908e"     # Find Matches
    ]
    for link in shortcut_links:
        webbrowser.open(link)
        # Small delay to prevent the OS from choking on 6 rapid requests
        time.sleep(1)

finally:
    # Stop animation
    fetch_done = True
    t.join()

input(f"Once you have accepted all 6 Shortcut installations, press RETURN/ENTER to continue.")

# -- SET UP SHORTCUTS CONFIG FILE --
print(f"")
print(f"SHORTCUTS CONFIG FILE SETUP")
print(f"  ℹ️  Configuring parameters file for Shortcuts to talk to your server.")
print(f"  🔐 Your SSH password or key will NOT be requested.")
print(f"  Enter basic SSH info...")


def get_host() -> str:
    host: str = input(
        f"  - Enter SSH host URL (e.g. 192.168.1.100 or myinstance.ydns.eu): ").strip().lower()
    if host == "":
        print(f"    ERROR: Host cannot be blank.")
        return get_host()
    return host


def get_port() -> str:
    port: str = input(
        f"  - Enter SSH port (e.g. 22)                                     : ").strip()
    if port.isnumeric() is False:
        print(f"    ERROR: Port must be a number.")
        return get_port()
    if port == "":
        print(f"    ERROR: Port cannot be blank.")
        return get_port()
    return port


def get_user() -> str:
    user: str = input(
        f"  - Enter SSH username (e.g. root)                               : ").strip().lower()
    if user == "":
        print(f"    ERROR: Username cannot be blank.")
        return get_user()
    return user


host = get_host().strip()
port = get_port().strip()
user = get_user().strip()


# Get filepath of this script
#   .resolve() ensures it's the full path, .parent removes the filename, .parent gets out of `setup/`
home_dir = Path(__file__).resolve().parent.parent
home_dir_str = str(home_dir)

# Write filepath into Shortcuts file, for each Shortcut to read from
icloud_shortcuts_dir = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents")
# Create the directory if it somehow doesn't exist
os.makedirs(icloud_shortcuts_dir, exist_ok=True)

# Assemble all info going into file
info_dict = {
    "home_dir": home_dir_str,
    "ssh_host": host,
    "ssh_port": port,
    "ssh_user": user
}

# Write and save the file (Note: You can safely change .txt to .json if you prefer)
write_file_path = os.path.join(
    icloud_shortcuts_dir, "petsafe_shortcut_config.txt")

with open(write_file_path, "w") as f:
    # json.dumps converts the dictionary to a string with double quotes
    f.write(json.dumps(info_dict, indent=4))

# -- WRAP UP FILE SETUP --
print(f"✅ Success: Directory path saved to Shortcuts iCloud folder. Shortcuts will access it at:")
print(f"{write_file_path}")


# -- GIVE INSTRUCTIONS TO WALK THROUGH SHORTCUTS SETUP --
print(f"")
print(f"NEXT STEPS FOR SHORTCUTS (also viewable in README.md):")
print(f"To finish setup, you must manually complete a few steps on your Apple device.")
print(f"This is required by Apple for your security and cannot be automated.")
print(f"1. Enable Scripting:")
print(f"   - On Mac: Open Shortcuts > Settings > Advanced > check 'Allow Running Scripts'")
print(f"   - On iOS: Open Settings app > Apps > Shortcuts > Advanced > enable 'Allow Running Scripts'")
print(f"2. Add SSH Credentials in the Shortcuts App:")
print(f"   - Open the Shortcuts app and edit the shortcuts.")
print(f"   - Scroll down to the 'Run script over SSH' action.")
print(f"   - Expand the action and under 'Authentication', choose 'SSH Key' (default) or 'Password'.")
print(f"   - If you use a password to SSH into your device:")
print(f"     - In each black-and-white 'Run Scripts Over SSH' module in shortcuts, change Authentication to 'Password':")
print(f"       'Petsafe View' shortcut            | 1 instance")
print(f"       'Petsafe Remove' shortcut          | 1 instance")
print(f"       'Petsafe Remove Matches' shortcut  | 3 instances")
print(f"       'Petsafe Add' shortcut             | 8 instances")
print(f"     - Enter your password directly into the new Password field.")
print(f"   - If you use an SSH key:")
print(f"     - See README.md for more details.")
print(f"   - 🔐 We do not ask for your password or SSH key so it stays securely on your device.")
print(f"3. Grant First-Run Permissions:")
print(f"   - Run the 'PetSafe' shortcut for the first time.")
print(f"   - As you go through the prompts, you will see several one-time security pop-ups:")
print(f"     * 'Allow PetSafe to run another shortcut?' -> click 'Allow'")
print(f"     * 'Allow PetSafe to use 1 text item in an SSH script...' -> click 'Always Allow'")
print(f"")
input(f"Press RETURN/ENTER to acknowledge and continue.")

# -- Print footers --
width = 36
message = "APPLE SHORTCUTS SETUP: COMPLETE"
print(f"." * width)
print(f"|" + message.center(width-2) + "|")
print(f"=" * width)
print(f"")
