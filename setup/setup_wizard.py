#!/usr/bin/python3

import os
import subprocess
import sys


# Check OS
if os.name != 'posix':
    # sys.exit() is cleaner than raising a raw Exception for end-users
    sys.exit(
        f"FATAL ERROR: This script requires a Unix-based OS (including macOS and Raspberry Pi). Detected: {os.name})")

# Run setup_auth.py
subprocess.run(["python3", "setup/setup_auth.py"])

# Run setup_feeders_map.py
subprocess.run(["python3", "setup/setup_feeders_map.py"])

# Run setup_shortcuts.py
subprocess.run(["python3", "setup/setup_shortcuts.py"])
