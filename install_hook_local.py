#!/usr/bin/env python3

import os
import shutil
import datetime

PYTHON_SCRIPT = "check_secrets.py"
CONFIG_FILE = "securegit.json"


def main():
  git_dir = os.path.join(".git", "hooks")
  hook_path = os.path.join(git_dir, "pre-commit")
  config_path = os.path.join(".git", "securegit.json")

  if not os.path.isdir(git_dir):
    print("❌ Not a git repository!")
    return

  if not os.path.exists(PYTHON_SCRIPT):
    print(f"❌ Cannot find {PYTHON_SCRIPT}. Please make sure it exists.")
    return

  if not os.path.exists(CONFIG_FILE):
    print(f"❌ Cannot find {CONFIG_FILE}. Please make sure it exists.")
    return

  if os.path.exists(hook_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{hook_path}.bak.{timestamp}"
    shutil.copyfile(hook_path, backup_path)

    print(f"⚠️ Existing pre-commit hook found and backed up to: {backup_path}")
    print("⚠️ Installing this hook will replace your existing pre-commit hook.")

    response = input("Do you want to continue? (y/N): ").strip().lower()
    if response != 'y':
      print("❌ Installation aborted.")
      return

  shutil.copyfile("check_secrets.py", hook_path)
  os.chmod(hook_path, 0o775)

  shutil.copyfile("securegit.json", config_path)

  print("✅ Pre-commit hook and configuration installed successfully!")


if __name__ == "__main__":
  main()
