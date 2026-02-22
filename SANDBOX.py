from pathlib import Path

# Path(__file__) gets the current file location
# .resolve() turns it into an absolute/full path
full_path = Path(__file__).resolve()

print(full_path)
