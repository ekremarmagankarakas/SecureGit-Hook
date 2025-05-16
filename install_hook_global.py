#!/usr/bin/env python3

import os
import shutil
import subprocess
import datetime

PYTHON_SCRIPT = "check_secrets.py"
CONFIG_FILE = "securegit.json"


def main():
  template_hooks_dir = os.path.expanduser("~/.git-templates/hooks")
  destination_hook = os.path.join(template_hooks_dir, "pre-commit")
  global_config_path = os.path.expanduser("~/.config/securegit")
  global_config_file = os.path.join(global_config_path, "securegit.json")

  if not os.path.exists(PYTHON_SCRIPT):
    print(f"❌ Cannot find {PYTHON_SCRIPT}. Please make sure it exists.")
    return

  if not os.path.exists(CONFIG_FILE):
    print(f"❌ Cannot find {CONFIG_FILE}. Please make sure it exists.")
    return

  os.makedirs(template_hooks_dir, exist_ok=True)
  print(
      f"📂 Ensured git template hooks directory exists at {template_hooks_dir}")

  os.makedirs(global_config_path, exist_ok=True)
  print(f"📂 Ensure global config directory exists at {global_config_path}")

  if os.path.exists(destination_hook):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{destination_hook}.bak.{timestamp}"
    shutil.copyfile(destination_hook, backup_path)

    print(f"⚠️ Existing pre-commit hook found and backed up to: {backup_path}")
    print("⚠️ Installing this hook will replace your existing global pre-commit hook.")

    response = input("Do you want to continue? (y/N): ").strip().lower()
    if response != 'y':
      print("❌ Installation aborted.")
      return

  shutil.copyfile(PYTHON_SCRIPT, destination_hook)
  os.chmod(destination_hook, 0o775)
  print(f"✅ Copied pre-commit hook to {destination_hook}")

  subprocess.run(["git", "config", "--global", "init.templateDir",
                 os.path.expanduser("~/.git-templates")], check=True)
  print("🔧 Set git global init.templateDir to ~/.git-templates")

  shutil.copyfile(CONFIG_FILE, global_config_file)
  print(f"✅ Copied config file to {global_config_file}")

  print("\n🚀 All set! Now every time you run 'git init', your pre-commit hook will be auto-installed.")


if __name__ == "__main__":
  main()
