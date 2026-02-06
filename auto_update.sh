#!/bin/bash

# 1. Go to the project directory (Corrected Path)
cd ***REDACTED*** || exit

# 2. Pull the latest changes silently
# We log output to a file inside the directory so you can debug later
git pull origin main >> ***REDACTED***/git_update.log 2>&1
