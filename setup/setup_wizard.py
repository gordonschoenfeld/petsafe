#!/usr/bin/python3

import os
import subprocess
import sys


# Check OS; stop if not Unix-based
if os.name != 'posix':
    sys.exit(
        f"FATAL ERROR: This script requires a Unix-based OS (including macOS and Raspberry Pi). Detected: {os.name})")

# Run setup_auth.py
subprocess.run(["python3", "setup/setup_auth.py"])

# Run setup_feeders_map.py
subprocess.run(["python3", "setup/setup_feeders_map.py"])

# Run setup_shortcuts.py
subprocess.run(["python3", "setup/setup_shortcuts.py"])
