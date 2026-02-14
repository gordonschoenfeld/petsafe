#!/usr/bin/python3

import subprocess

# ...FYI on how to run...
# # Execution with arguments
# subprocess.run(["python3", "other_script.py", "arg1", "--flag"])

# # Capture the output to a variable
# result = subprocess.run(
#     ["python3", "other_script.py"],
#     capture_output=True,
#     text=True
# )
# print(f"Script output: {result.stdout}")


# Run setup_auth.py
subprocess.run(["python3", "setup/setup_auth.py"])

# Run setup_feeders_map.py
subprocess.run(["python3", "setup/setup_feeders_map.py"])
