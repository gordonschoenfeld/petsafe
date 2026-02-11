#!/usr/bin/python3

from datetime import date
import sys


def compute_date_diff(date1: str, date2: str) -> int:
    """
    Calculates the days between two MM/DD strings, assuming the 'next' 
    occurrence for both relative to the current calendar year.
    """
    today = date.today()
    current_year = today.year

    def parse_to_next_date(md_str):
        month, day = map(int, md_str.split('/'))
        # Create the date for the current year
        d = date(current_year, month, day)

        # If that date is in the past, move it to next year
        if d < today:
            d = d.replace(year=current_year + 1)
        return d

    d1 = parse_to_next_date(date1)
    d2 = parse_to_next_date(date2)

    return (d2 - d1).days


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: compute_date_diff <start_date> <end_date>", file=sys.stderr)
        print("Dates must be in MM/DD format, with leading zeroes.", file=sys.stderr)
        sys.exit(1)
    else:
        try:
            start_date = sys.argv[1]
            end_date = sys.argv[2]
            result = compute_date_diff(start_date, end_date)
            print(result)
        except ValueError:
            print("Invalid date format. Please use MM/DD.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)
