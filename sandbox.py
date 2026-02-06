#!/usr/bin/env python3

import sys

# sys.argv[0] is the script name, sys.argv[1] is the first argument passed
if len(sys.argv) > 1:
    amount = int(sys.argv[1])  # Convert string input to integer
else:
    amount = 10  # Default fallback

print(f"Feeding {amount} portions...")
# feed_pet(amount)
