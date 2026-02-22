import itertools
import sys
import threading
import time
import webbrowser


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

# Opt-in
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


# Present Info text and prompt to continue
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
        # "https://www.icloud.com/shortcuts/0cf5f0c06f6d4f7f8e8d59c2fd705e0a",    # PetSafe
        # "https://www.icloud.com/shortcuts/5fe0d58baaf1432d870a2438e8bbca27",    # Add
        # "https://www.icloud.com/shortcuts/cdf087d017884c0c9aafea22fbb42bae",    # Remove
        # "https://www.icloud.com/shortcuts/3b83f601cf54496dab14d93579ae4eb3",    # View
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
# TODO: pull it and write it into iCloud?!?
#       - plan B: Guide through the establishing the filepath

# -- Print footers --
width = 36
message = "APPLE SHORTCUTS SETUP: COMPLETE"
print(f"." * width)
print(f"|" + message.center(width-2) + "|")
print(f"=" * width)
print(f"")
