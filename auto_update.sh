#!/bin/bash

# Copyright (c) 2026 Gordon Schoenfeld
# Licensed under the MIT License.
# See LICENSE file in the project root for full license information.

# ABOUT
# This script keeps the server's code up to date.
# This script runs a `git pull`.

# 1. Get project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 2. Go to the project directory
cd $SCRIPT_DIR || exit

# 3. Pull the latest changes and log output to a file so you can debug later
echo "$(date "+%Y-%m-%d %H:%M") - Starting update" >> $SCRIPT_DIR/logs/git_update.log
git pull origin main >> $SCRIPT_DIR/logs/git_update.log 2>&1
