# SecureGit-Hook

A robust Git pre-commit hook that scans your code for hardcoded secrets, API keys, tokens, and credentials before they're committed to your repository.

## Overview

SecureGit-Hook is a security-focused tool that helps prevent sensitive information from being accidentally committed to your Git repositories. It scans staged files for patterns that look like credentials, API keys, and other secrets.

## Features

- **Comprehensive pattern detection**: Identifies over 30 different types of secrets and credentials
- **Prohibited file detection**: Prevents committing common files that typically contain secrets (.env files, key files, etc.)
- **Multiple installation options**: Install per-repository or globally across all your Git repositories
- **Support for multiple file types**: Scans a wide variety of file formats including Python, JavaScript, TypeScript, Go, configuration files, and more
- **Override capability**: Provides an option to override the hook when necessary, with clear warnings
- **Easy installation**: Simple setup scripts for both individual and global installation

## What It Detects

### Detected Secret Patterns

SecureGit-Hook detects a wide range of sensitive information, including:

- Generic API keys, tokens and secrets
- Passwords and credentials
- AWS access keys and secrets
- Database connection strings
- GitHub tokens
- Stripe API keys
- PayPal credentials
- Google API and OAuth tokens
- JWT tokens
- Private keys and certificates
- Slack API tokens
- Heroku credentials
- SSH keys
- OpenAI API keys
- And many more

### Prohibited Files

SecureGit-Hook also prevents accidental commits of files that typically contain sensitive information:

- `.env` files and variants
- Credential and configuration files
- Private key files
- Keystores and certificates
- Token files

## Installation

### Per-Repository Installation

To install the pre-commit hook in your current repository:

```bash
python install_hook.py
```

This will install the hook only for the current Git repository.

### Global Installation

To install the pre-commit hook globally for all future Git repositories:

```bash
python install_hook_global.py
```

This will:
1. Create a Git templates directory
2. Configure Git to use this template directory
3. Place the pre-commit hook in the templates directory
4. Automatically add the hook to any new repository you initialize with `git init`

## Usage

Once installed, the hook runs automatically when you attempt to make a commit. If potential secrets are detected:

1. The commit will be blocked
2. You'll see a list of files and line numbers containing potential secrets
3. You'll be given the option to:
   - Cancel the commit (recommended)
   - Override the check by typing 'OVERRIDE' (use with caution)

Example output:
```
=
 Scanning 3 file(s)...

L Hardcoded secrets found in config.py:
  � Line 12: API_KEY = "abc123xyz456"
  � Line 15: PASSWORD = "supersecret"

=� Commit contains potential hardcoded secrets!

Type 'OVERRIDE' to bypass and commit anyway, or anything else to cancel:
```

## Supported File Types

The hook scans files with the following extensions:
- `.py` (Python)
- `.js` (JavaScript)
- `.ts` (TypeScript)
- `.go` (Go)
- `.env` (Environment files)
- `.json` (JSON)
- `.yaml`, `.yml` (YAML)
- `.xml` (XML)
- `.conf` (Configuration files)
- `.ini` (INI files)
- `.toml` (TOML files)
- `.rb` (Ruby)
- `.php` (PHP)

## How It Works

When you attempt to make a Git commit:

1. The pre-commit hook is triggered
2. The hook scans all staged files with supported extensions
3. Each file is checked against a large set of regular expressions designed to detect secrets
4. If matches are found, the commit is blocked with detailed information about the findings
5. You must either fix the issues or explicitly override the check

## Best Practices

- **Never commit secrets**: Use environment variables or dedicated secret management solutions
- **Use `.env` files**: Store secrets in `.env` files that are included in your `.gitignore`
- **Employ `.gitignore`**: Always add files containing secrets to your `.gitignore`
- **Consider credential managers**: Use dedicated services like AWS Secrets Manager, HashiCorp Vault, etc.
- **Rotate compromised secrets**: If you accidentally commit a secret, consider it compromised and rotate it immediately

## Troubleshooting

### The hook isn't running when I commit

Make sure:
- The hook is properly installed (check `.git/hooks/pre-commit` exists and is executable)
- Your Git is configured to use hooks (not disabled globally)
- Python is available in your PATH

### I need to bypass the hook temporarily

Use the `--no-verify` flag with your Git commit command:
```bash
git commit --no-verify -m "Your commit message"
```
But remember, this bypasses ALL pre-commit hooks, not just the secrets check.

### I get false positives

The scanning patterns are intentionally aggressive to minimize the risk of leaking secrets. If you're getting many false positives:
1. Consider modifying the `PATTERNS` list in `check_secrets.py` to suit your specific needs
2. For test files or examples with fake credentials, use the override feature when necessary

## Contributing

Contributions are welcome! Here are some ways you can contribute:
- Add new detection patterns
- Improve existing patterns to reduce false positives
- Add support for additional file types
- Enhance the user interface or reporting

## Disclaimer

While this tool aims to prevent the accidental committing of secrets, it is not foolproof. Always manually review your code and commits, especially for sensitive repositories. The maintainers are not responsible for any secrets that might slip through the detection patterns.