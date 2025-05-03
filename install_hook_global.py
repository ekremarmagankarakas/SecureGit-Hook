#!/usr/bin/env python3

import os
import shutil
import subprocess

# Your Python script that will act as the pre-commit hook
PYTHON_SCRIPT = "check_secrets.py"

def main():
    template_hooks_dir = os.path.expanduser("~/.git-templates/hooks")

    # Step 1: Create the template hooks directory if it doesn't exist
    os.makedirs(template_hooks_dir, exist_ok=True)
    print(f"📂 Ensured git template hooks directory exists at {template_hooks_dir}")

    # Step 2: Copy your Python script as the pre-commit hook
    if not os.path.exists(PYTHON_SCRIPT):
        print(f"❌ Cannot find {PYTHON_SCRIPT}. Please make sure it exists.")
        return

    destination_hook = os.path.join(template_hooks_dir, "pre-commit")
    shutil.copyfile(PYTHON_SCRIPT, destination_hook)
    os.chmod(destination_hook, 0o775)
    print(f"✅ Copied pre-commit hook to {destination_hook}")

    # Step 3: Configure git to use this template
    subprocess.run(["git", "config", "--global", "init.templateDir", os.path.expanduser("~/.git-templates")], check=True)
    print("🔧 Set git global init.templateDir to ~/.git-templates")

    print("\n🚀 All set! Now every time you run 'git init', your pre-commit hook will be auto-installed.")

if __name__ == "__main__":
    main()