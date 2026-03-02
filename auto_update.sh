#!/bin/bash

# Copyright (c) 2026 Gordon Schoenfeld
# Licensed under the MIT License.
# See LICENSE file in the project root for full license information.

# ABOUT
# This script keeps the server's code up to date.
# This script runs a `git pull`.

# 1. Go to the project directory
cd ***REDACTED*** || exit

# 2. Pull the latest changes silently
# We log output to a file inside the directory so you can debug later
echo "$(date "+%Y-%m-%d %H:%M") - Starting update" >> ***REDACTED***/logs/git_update.log
git pull origin main >> ***REDACTED***/logs/git_update.log 2>&1
