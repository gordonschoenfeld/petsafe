#!/bin/bash

# ABOUT: This script keeps the server's code up to date.
# This script runs a `git pull`.

# 1. Go to the project directory
cd ***REDACTED*** || exit

# 2. Pull the latest changes silently
# We log output to a file inside the directory so you can debug later
sed -i 's/^/$(date "+%Y-%m-%d %H:%M") /' ***REDACTED***/git_updates.log
git pull origin main >> ***REDACTED***/git_update.log 2>&1
