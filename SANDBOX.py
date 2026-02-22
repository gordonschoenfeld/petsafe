from pathlib import Path

# .resolve() ensures it's the full path, .parent removes the filename
script_dir = Path(__file__).resolve().parent

print(script_dir)
