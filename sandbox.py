#!/usr/bin/env python3

import subprocess
from datetime import datetime
import re


def compute_date_diff(date1: tuple | str, date2: tuple | str) -> int | None:
    # 1. Convert Tuple inputs ('MM', 'DD') to String "MM/DD". subprocess.run cannot handle tuples directly.
    if isinstance(date1, tuple):
        date1 = f"{date1[0]}/{date1[1]}"

    if isinstance(date2, tuple):
        date2 = f"{date2[0]}/{date2[1]}"

    try:
        # 2. Run the external script
        result = subprocess.run(
            ['python3', 'compute_date_diff.py', date1, date2],  # Ensure python3
            capture_output=True,
            text=True,
            check=True
        )

        # 3. Return the result as an integer
        print(int(result.stdout.strip()))

    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e.stderr}")
        return None
    except ValueError:
        print(f"Error: Script returned non-integer: {result.stdout}")
        return None


def get_date(clarifying_text: str = None) -> tuple[str] | None:
    def normalize_date(date_str: str) -> tuple[str]:
        # Regex Breakdown:
        # 1. (0?[1-9]|1[0-2]) : Capture Group 1 (Month) - 1-12, optional leading zero
        # 2. \/?              : Optional Slash (ignored)
        # 3. (0?[1-9]|[12]\d|3[01]) : Capture Group 2 (Day) - 1-31, optional leading zero

        match = re.match(
            r'^(0?[1-9]|1[0-2])\/?(0?[1-9]|[12]\d|3[01])$', date_str)

        if match:
            month, day = match.groups()

            # Enforce 4-digit logic: if input was "0809", regex splits it correctly.
            # If input was "89", regex might match (8, 9), but that is usually ambiguous.
            # This regex assumes standard separators or clear 4-digit blocks.

            # Return tuple with leading zeros
            return (month.zfill(2), day.zfill(2))
        else:
            return None

    def validate_date(date_str: str, now=None) -> tuple[str]:
        # Regex Breakdown (3 Distinct Branches):
        # 1. Slash Required:  8/9, 08/09, 12/31
        # 2. 4-Digit Strict:  0809, 1231
        # 3. 2-Digit Strict:  12 (splits to 1/2), 89 (splits to 8/9)
        #    Note: Uses [1-9] to ensure we don't match "10" (Day 0 is invalid)

        pattern = (
            r'^(?:'
            r'(0?[1-9]|1[0-2])\/(0?[1-9]|[12]\d|3[01])|'  # Branch 1: Slash
            r'(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])|'      # Branch 2: 4-Digit
            r'([1-9])([1-9])'                             # Branch 3: 2-Digit
            r')$'
        )

        match = re.match(pattern, date_str)

        if not match:
            raise ValueError(
                f"Invalid format: '{date_str}'. Accepted: M/D, MMDD, or MD.")

        # Extract groups. The regex has 6 groups total (2 per branch).
        # We find the pair that isn't None.
        g = match.groups()
        month_str = g[0] or g[2] or g[4]
        day_str = g[1] or g[3] or g[5]

        month, day = int(month_str), int(day_str)

        if now is None:
            now = datetime.now()

        try:
            candidate_date = datetime(now.year, month, day, 12, 0, 0)
        except ValueError:
            if month == 2 and day == 29:
                candidate_date = None
            else:
                raise ValueError(f"Invalid calendar date: {month}/{day}")

        if candidate_date is None or candidate_date < now:
            try:
                candidate_date = datetime(now.year + 1, month, day, 12, 0, 0)
            except ValueError:
                raise ValueError(
                    f"Date {month}/{day} does not exist in the upcoming year.")

        return candidate_date

    if clarifying_text:
        raw_date_input = input(
            f"Enter {clarifying_text} date (MM/DD), or 'NONE': ").strip().lower()
    else:
        raw_date_input = input(
            f"Enter date (MM/DD), or 'NONE': ").strip().lower()

    # escape hatch
    if raw_date_input in ['exit', 'x', 'quit', 'q']:
        print("Exiting program.")
        exit()
    # allow none
    if raw_date_input.strip().lower() in ['never', 'none', 'no', 'n', '']:
        return None

    # 1. VALIDATE the raw string (e.g., "8/9")
    # Do NOT pass a tuple here.
    if not validate_date(raw_date_input):
        print("Invalid format.")
        return None

    # 2. NORMALIZE after validation is successful
    # This turns "8/9" into ('08', '09')
    clean_date = normalize_date(raw_date_input)

    # return valid date
    return clean_date


today = (datetime.now().strftime('%m'), datetime.now().strftime('%d'))

test_date = get_date()

compute_date_diff(today, test_date)
