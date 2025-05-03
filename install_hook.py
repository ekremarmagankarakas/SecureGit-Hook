#!/usr/bin/env python3

import os
import shutil

def main():
    git_dir = os.path.join(".git", "hooks")
    hook_path = os.path.join(git_dir, "pre-commit")

    if not os.path.isdir(git_dir):
        print("❌ Not a git repository!")
        return

    # Copy the check_secrets.py directly as the pre-commit hook
    shutil.copyfile("check_secrets.py", hook_path)
    os.chmod(hook_path, 0o775)

    print("✅ Pre-commit hook installed successfully!")

if __name__ == "__main__":
    main()