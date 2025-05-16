#!/usr/bin/env python3

import subprocess
import re
import sys
import os
import json


def load_config():
  """Load configuration from securegit.json file if it exists."""

  # Look for config file in the following locations:
  config_paths = [
      # Local repository config
      os.path.join(os.getcwd(), "securegit.json"),
      # Global user config
      os.path.expanduser("~/.securegit.json"),
  ]

  config_path = ""
  for path in config_paths:
    if os.path.exists(path):
      config_path = path
      break

  if config_path == "":
    print("❌ No config file found. Not checking for any leakages.")
    sys.exit(0)

  # Load and parse the JSON config file
  try:
    with open(config_path, 'r') as f:
      config = json.load(f)
      return config
  except (json.JSONDecodeError, IOError) as e:
    print(f"⚠️ Error loading config file: {e}")
    sys.exit(1)


def get_staged_files():
  result = subprocess.run(
      ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
      stdout=subprocess.PIPE,
      text=True,
  )
  files = result.stdout.strip().split("\n")
  return [f for f in files if f]


def get_all_repo_files():
  """Get all files tracked by git in the repository."""
  result = subprocess.run(
      ["git", "ls-files"],
      stdout=subprocess.PIPE,
      text=True,
  )
  files = result.stdout.strip().split("\n")
  return [f for f in files if f]


def is_allowlisted(filepath, line_num=None, match_text=None, config=None):
  """
  Check if a file, line, or pattern match is allowlisted.

  Args:
      filepath: Path to the file being checked
      line_num: Line number in the file (optional)
      match_text: The text that matched a pattern (optional)
      config: Configuration dictionary

  Returns:
      True if the item is allowlisted, False otherwise
  """
  if not config or "allowlist" not in config:
    return False

  allowlist = config["allowlist"]

  # Check if the exact file is in the file allowlist
  if filepath in allowlist.get("files", []):
    return True

  # Check if the file is in an allowlisted path
  for path in allowlist.get("paths", []):
    if filepath.startswith(path) or re.match(path, filepath):
      return True

  # Check for specific line allowlist
  if line_num is not None:
    line_key = f"{filepath}:{line_num}"
    if line_key in allowlist.get("lines", []):
      return True

  # Check if the match text is in the patterns allowlist
  if match_text is not None:
    for pattern in allowlist.get("patterns", []):
      if re.search(pattern, match_text):
        return True

  return False


def check_prohibited_files(files, config):
  prohibited_found = []
  
  # Get lists from config with fallbacks to empty lists
  prohibited_files = config.get("prohibited_files", [])
  prohibited_patterns = config.get("prohibited_patterns", [])

  for file in files:
    # Skip allowlisted files
    if is_allowlisted(file, config=config):
      continue

    # Check exact filenames
    filename = os.path.basename(file)
    if filename in prohibited_files:
      prohibited_found.append((file, "File should not be committed"))
      continue

    # Check regex patterns
    for pattern in prohibited_patterns:
      if re.match(pattern, file):
        prohibited_found.append((file, "File matches prohibited pattern"))
        break

  return prohibited_found


def scan_file(filepath, config):
  findings = []
  try:
    with open(filepath, "r", encoding="utf-8") as file:
      content = file.read()
      line_num = 1

      # Check if the entire file is allowlisted
      if is_allowlisted(filepath, config=config):
        return []

      # Get patterns from config with fallback to empty list
      patterns = config.get("patterns", [])

      for line in content.split("\n"):
        # Skip allowlisted specific lines
        if is_allowlisted(filepath, line_num, config=config):
          line_num += 1
          continue

        for pattern in patterns:
          try:
            matches = re.findall(pattern, line)
            if matches:
              for match in matches:
                # If the match is a tuple (from capture groups), take the first element
                match_value = match[0] if isinstance(match, tuple) else match

                # Skip allowlisted patterns
                if is_allowlisted(filepath, line_num, match_value, config):
                  continue

                findings.append((line_num, match_value))
          except re.error as re_err:
            print(f"⚠️ Invalid regex pattern '{pattern}': {re_err}")
        line_num += 1
  except Exception as e:
    print(f"⚠️ Could not read {filepath}: {e}")
  return findings


def main():
  # Load configuration
  config = load_config()

  # Check if hook is disabled in config
  if "enabled" in config and not config["enabled"]:
    print("✅ SecureGit-Hook is disabled in configuration. Skipping checks.")
    sys.exit(0)

  if "scan_entire_repo" in config and config["scan_entire_repo"]:
    files = get_all_repo_files()
    print("🔍 Scanning entire repository as configured...")
  else:
    files = get_staged_files()

  if not files or files == [""]:
    print("✅ No relevant files staged.")
    return

  print(f"🔍 Scanning {len(files)} file(s)...")

  # First check for prohibited files
  prohibited = check_prohibited_files(files, config)
  if prohibited:
    print("\n⚠️ WARNING: The following files should not be committed:")
    for file, reason in prohibited:
      print(f"  → {file}: {reason}")
    print("❌ Commit aborted. Please remove these files.")
    sys.exit(1)

  # Filter for valid extensions for secret scanning
  valid_extensions = config.get("valid_extensions", [])
  files_to_scan = [
      f for f in files if any(f.endswith(ext) for ext in valid_extensions)
  ]

  any_findings = False

  for file in files_to_scan:
    matches = scan_file(file, config)
    if matches:
      any_findings = True
      print(f"\n❌ Hardcoded secrets found in {file}:")
      for line_num, match in matches:
        print(f"  → Line {line_num}: {match}")

  if any_findings:
    print("\n🚫 Commit contains potential hardcoded secrets!")
    print("❌ Commit aborted. Clean your code before committing.")
    sys.exit(1)
  else:
    print("✅ No hardcoded secrets found.")


if __name__ == "__main__":
  main()
