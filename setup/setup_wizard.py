#!/usr/bin/python3

import subprocess

# Run setup_auth.py
subprocess.run(["python3", "setup/setup_auth.py"])

# Run setup_feeders_map.py
subprocess.run(["python3", "setup/setup_feeders_map.py"])
