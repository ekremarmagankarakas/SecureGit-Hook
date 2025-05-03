#!/usr/bin/env python3

import subprocess
import re
import sys
import os
import json

# Default configuration values
DEFAULT_CONFIG = {
    "enabled": True,
    "valid_extensions": [
        ".py",
        ".js",
        ".ts",
        ".go",
        ".env",
        ".json",
        ".yaml",
        ".yml",
        ".xml",
        ".conf",
        ".ini",
        ".toml",
        ".rb",
        ".php",
    ],
    "prohibited_files": [
        ".env",
        ".env.local",
        ".env.development",
        ".env.test",
        ".env.production",
        "credentials.json",
        "config.local.json",
        "secrets.yaml",
        ".htpasswd",
        "id_rsa",
        "id_dsa",
        ".keystore",
        ".p12",
        ".pfx",
        "oauth_token.json",
        "service-account.json",
    ],
    "prohibited_patterns": [
        r".*\.pem$",
        r".*\.key$",
        r".*\.pkcs12$",
        r".*\.jks$",
        r".*secret.*\.json$",
        r".*password.*\.txt$",
        r".*credential.*\.json$",
        r".*\.keystore$",
    ],
    "patterns": [
        # Generic secret variables
        r'API_KEY\s*=\s*["\'].*["\']',
        r'SECRET\s*=\s*["\'].*["\']',
        r'PASSWORD\s*=\s*["\'].*["\']',
        r'TOKEN\s*=\s*["\'].*["\']',
        r'PASSW(OR)?D\s*=\s*["\'].*["\']',
        r'PWD\s*=\s*["\'].*["\']',
        r'PASSWD\s*=\s*["\'].*["\']',
        r'KEY\s*=\s*["\'].*["\']',
        r'APIKEY\s*=\s*["\'].*["\']',
        r'AUTH\s*=\s*["\'].*["\']',
        r'CREDENTIAL\s*=\s*["\'].*["\']',
        r'PRIVATE_KEY\s*=\s*["\'].*["\']',
        # Common credential formats
        r'(access|secret|api|auth|client|token)[-._]?(key|secret|token|id|password)[\s=:]+["\']?[A-Za-z0-9+/]{8,}["\']?',
        # AWS
        r"(AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{12,}",  # AWS Access Key ID
        r'aws[._-]?access[._-]?key[._-]?id\s*=\s*["\']?\w+["\']?',
        r'aws[._-]?secret[._-]?access[._-]?key\s*=\s*["\']?\w+["\']?',
        r'aws[._-]?account[._-]?id\s*=\s*["\']?\d+["\']?',
        # Database connection strings
        r"(?i)(jdbc|mongodb(\+srv)?|mysql|postgres|postgresql|mssql|sqlite|redis|oracle):\/\/[a-zA-Z0-9]+:[^@]+@",
        r"(?i)mongodb[+:].*(?:username|password).*:",
        r"(?i)(host|server|db|database|username|user|uid|password|pwd|passwd)[\s=:]",
        r'(?i)connection[._-]string\s*=\s*["\'].*["\']',
        # API keys and tokens with characteristic patterns
        r"gh[pousr]_[A-Za-z0-9_]{16,}",  # GitHub tokens
        r"sk_live_[0-9a-zA-Z]{24,}",  # Stripe API keys
        r"rk_live_[0-9a-zA-Z]{24,}",  # Stripe restricted keys
        r"sq0atp-[0-9A-Za-z\-_]{22}",  # Square Access Token
        r"sq0csp-[0-9A-Za-z\-_]{43}",  # Square API key
        r"access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}",  # PayPal Access Token
        r"amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",  # Amazon MWS Auth Token
        r"EAACEdEose0cBA[0-9A-Za-z]+",  # Facebook Access Token
        r"AIza[0-9A-Za-z\-_]{35}",  # Google API Key
        r"ya29\.[0-9A-Za-z\-_]+",  # Google OAuth
        r"sk-[A-Za-z0-9]{32,}",  # OpenAI API key
        # JWT Tokens
        r"ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]{10,}\.[A-Za-z0-9_-]{10,}",  # JWT
        # Certificates and private keys
        r"-----BEGIN [A-Z ]+ PRIVATE KEY( BLOCK)?-----",
        r"-----BEGIN CERTIFICATE-----",
        # Slack
        r"xox[pboa]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32}",  # Slack API tokens
        # Heroku
        r"[h|H][e|E][r|R][o|O][k|K][u|U].*[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}",
        # Encryption keys
        r'(?i)(encryption|cipher|aes|rsa)[._-]?key\s*=\s*["\'].*["\']',
        # Twilio
        r"SK[0-9a-fA-F]{32}",  # Twilio API keys
        r"AC[a-z0-9]{32}",  # Twilio Account SID
        # SSH keys
        r"ssh-rsa AAAA[0-9A-Za-z+/]+[=]{0,3}",
        # Generic alphanumeric secrets
        r'(?i)(api|secret|private|token|auth|key)[\s=:]+["\']?[a-zA-Z0-9+/]{32,}[=]{0,2}["\']?',
    ],
}


def load_config():
    """Load configuration from securegit.json file if it exists."""
    config = DEFAULT_CONFIG.copy()

    # Look for config file in the following locations:
    config_paths = [
        # Local repository config
        os.path.join(os.getcwd(), "securegit.json"),
        # Global user config
        os.path.expanduser("~/.securegit.json"),
    ]

    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    print(f"🔧 Loaded configuration from {config_path}")

                    # Process configuration with the following priority:
                    # 1. Regular configs (direct replacement)
                    # 2. Exclusions (_exclude suffix)
                    # 3. Expansions (_expand suffix)

                    # First apply regular direct replacements
                    for key, value in user_config.items():
                        if not key.endswith("_exclude") and not key.endswith("_expand"):
                            if key in config:
                                config[key] = value

                    # Then apply exclusions
                    for key, value in user_config.items():
                        if key.endswith("_exclude") and isinstance(value, list):
                            base_key = key[:-8]  # Remove "_exclude" suffix
                            if base_key in config and isinstance(
                                config[base_key], list
                            ):
                                original_len = len(config[base_key])
                                # Remove items that match those in the exclude list
                                config[base_key] = [
                                    item
                                    for item in config[base_key]
                                    if item not in value
                                ]
                                removed = original_len - len(config[base_key])
                                print(f"  ↪ Excluded {removed} items from {base_key}")

                    # Finally apply expansions
                    for key, value in user_config.items():
                        if key.endswith("_expand") and isinstance(value, list):
                            base_key = key[:-7]  # Remove "_expand" suffix
                            # Only expand if it wasn't completely replaced by a direct config
                            if base_key in config and isinstance(
                                config[base_key], list
                            ):
                                config[base_key].extend(value)
                                print(
                                    f"  ↪ Expanded {base_key} with {len(value)} additional items"
                                )

                # Once we find a valid config, stop looking
                break
            except json.JSONDecodeError:
                print(
                    f"⚠️ Warning: Could not parse {config_path} as valid JSON. Using defaults."
                )
            except Exception as e:
                print(f"⚠️ Warning: Error loading config from {config_path}: {e}")

    return config


def get_staged_files():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        stdout=subprocess.PIPE,
        text=True,
    )
    files = result.stdout.strip().split("\n")
    return [f for f in files if f]


def check_prohibited_files(files, config):
    prohibited_found = []

    for file in files:
        # Check exact filenames
        filename = os.path.basename(file)
        if filename in config["prohibited_files"]:
            prohibited_found.append((file, "File should not be committed"))
            continue

        # Check regex patterns
        for pattern in config["prohibited_patterns"]:
            if re.match(pattern, file):
                prohibited_found.append((file, "File matches prohibited pattern"))
                break

    return prohibited_found


def scan_file(filepath, patterns):
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            line_num = 1
            for line in content.split("\n"):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    if matches:
                        for match in matches:
                            # If the match is a tuple (from capture groups), take the first element
                            match_value = (
                                match[0] if isinstance(match, tuple) else match
                            )
                            findings.append((line_num, match_value))
                line_num += 1
    except Exception as e:
        print(f"⚠️ Could not read {filepath}: {e}")
    return findings


def main():
    # Load configuration
    config = load_config()

    # Check if hook is disabled in config
    if not config["enabled"]:
        print("✅ SecureGit-Hook is disabled in configuration. Skipping checks.")
        sys.exit(0)

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
    files_to_scan = [
        f for f in files if any(f.endswith(ext) for ext in config["valid_extensions"])
    ]

    any_findings = False

    for file in files_to_scan:
        matches = scan_file(file, config["patterns"])
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
