#!/usr/bin/python3

import itertools
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
print(f"If you want, you can also install UI/Siri capability via Apple Shortcuts.")

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
        "https://www.icloud.com/shortcuts/0cf5f0c06f6d4f7f8e8d59c2fd705e0a",    # PetSafe
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
print(f"  Configuring parameters for Shortcuts to talk to your server.")
print(f"  Your SSH security key/password will NOT be requested.")
print(f"  Enter your SSH login credentials...")


def get_host() -> str:
    host: str = input(
        f"  - Enter SSH host URL (e.g. myinstance.ydns.eu): ").strip().lower()
    if host == "":
        print(f"    ERROR: Host cannot be blank.")
        return get_host()
    return host


def get_port() -> str:
    port: str = input(
        f"  - Enter SSH port (e.g. 22)                    : ").strip()
    if port.isnumeric() is False:
        print(f"    ERROR: Port must be a number.")
        return get_port()
    if port == "":
        print(f"    ERROR: Port cannot be blank.")
        return get_port()
    return port


def get_user() -> str:
    user: str = input(
        f"  - Enter SSH username                          : ").strip().lower()
    if user == "":
        print(f"    ERROR: Username cannot be blank.")
        return get_user()
    return user


host = get_host()
port = get_port()
user = get_user()


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
info_dict = {"home_dir": home_dir_str,
             "ssh_host": host,
             "ssh_port": port,
             "ssh_user": user}

# Write and save the file
write_file_path = os.path.join(
    icloud_shortcuts_dir, "petsafe_shortcut_config.txt")

with open(write_file_path, "w") as f:
    f.write(str(info_dict))

# -- WRAP UP FILE SETUP --
print(f"✅ Success: Directory path saved to Shortcuts iCloud folder. Shortcuts will access it at:")
print(f"{write_file_path}")


# -- GIVE INSTRUCTIONS TO WALK THROUGH SHORTCUTS SETUP --
# TODO: print inx (expect one-time pop-ups, etc.)
# TODO: Action needed within Shortcuts? Copy-paste for SSH keys?? Stress that this is for your security.
#       Ask Gemini to list what user needs to do.


# -- Print footers --
width = 36
message = "APPLE SHORTCUTS SETUP: COMPLETE"
print(f"." * width)
print(f"|" + message.center(width-2) + "|")
print(f"=" * width)
print(f"")
