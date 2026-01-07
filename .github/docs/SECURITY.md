# Security Guidelines

## Protected Files

The following files contain sensitive data and are **NEVER** committed to git:

### Environment Files
- `.env` - Your personal API keys and secrets
- `.env.*` (except `.env.example`) - Alternative configurations
- `.env.local`, `.env.backup` - Local backups

### Credential Files
- `*.key`, `*.pem`, `*.p12` - Certificate files
- `credentials.json` - Service account keys
- `secrets/`, `.secrets/` - Secret directories

### Backup Directory
- `.backup/` - Contains archived sensitive files and logs

## Setup Instructions

1. **Initial Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Verify Protection**
   ```bash
   git check-ignore .env
   # Should output: .env
   ```

3. **Never Commit**
   - Always check `git status` before committing
   - Ensure `.env` is not listed in changes
   - Use `.env.example` for documentation

## API Keys Required

Choose at least one provider:

- **Gemini API**: https://makersuite.google.com/app/apikey
- **Ollama**: Local installation (https://ollama.ai)
- **Nebius**: https://nebius.com
- **HuggingFace**: https://huggingface.co/settings/tokens

## Key Rotation

If you accidentally commit a key:

1. **Immediately revoke** the exposed key in the provider dashboard
2. Generate a new key
3. Update your `.env` file
4. Use `git filter-branch` or BFG Repo-Cleaner to remove from history
5. Force push (coordinate with team first!)

## Security Checklist

- [ ] `.env` file exists locally
- [ ] `.env` contains valid API key(s)
- [ ] `.env` is listed in `.gitignore`
- [ ] `git status` does not show `.env`
- [ ] `.env.example` has no real keys
- [ ] `.backup/` directory is ignored

## Questions?

Contact the maintainer if you have security concerns.
