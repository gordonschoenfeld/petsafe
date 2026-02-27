#!/usr/bin/python3

import os
import subprocess
import sys


# Check OS; stop if not Unix-based
if os.name != 'posix':
    sys.exit(
        f"FATAL ERROR: This script requires a Unix-based OS (including macOS and Raspberry Pi). Detected: {os.name})")

# Check for pip; install
import sys
import subprocess

try:
    # Try to import the module (the import name is dateutil, even though the package is python-dateutil)
    import dateutil
except ImportError:
    print("Missing 'python-dateutil'. Installing now...")
    # This runs: python3 -m pip install python-dateutil
    subprocess.check_call([sys.executable, "-m", "pip",
                          "install", "python-dateutil"])

    # Import it now that it's installed
    import dateutil
    print("Successfully installed 'python-dateutil'!")
    print("")

# Proceed with the rest of your imports
import petsafe_smartfeed as sf

# Run setup_auth.py
subprocess.run(["python3", "setup/setup_auth.py"])

# Run setup_feeders_map.py
subprocess.run(["python3", "setup/setup_feeders_map.py"])

# Run setup_shortcuts.py
subprocess.run(["python3", "setup/setup_shortcuts.py"])
