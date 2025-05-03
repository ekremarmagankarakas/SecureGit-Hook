#!/usr/bin/env python3

import os
import shutil
import datetime

def main():
    git_dir = os.path.join(".git", "hooks")
    hook_path = os.path.join(git_dir, "pre-commit")

    if not os.path.isdir(git_dir):
        print("❌ Not a git repository!")
        return

    # Check if pre-commit hook already exists
    if os.path.exists(hook_path):
        # Create backup with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = f"{hook_path}.bak.{timestamp}"
        shutil.copyfile(hook_path, backup_path)
        
        print(f"⚠️ Existing pre-commit hook found and backed up to: {backup_path}")
        print("⚠️ Installing this hook will replace your existing pre-commit hook.")
        
        response = input("Do you want to continue? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Installation aborted.")
            return

    # Copy the check_secrets.py directly as the pre-commit hook
    shutil.copyfile("check_secrets.py", hook_path)
    os.chmod(hook_path, 0o775)

    print("✅ Pre-commit hook installed successfully!")

if __name__ == "__main__":
    main()