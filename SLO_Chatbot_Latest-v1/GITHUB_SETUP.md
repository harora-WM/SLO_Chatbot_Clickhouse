# GitHub Setup Instructions

## Authentication Required

To push to GitHub, you need to authenticate. Choose one of the methods below:

### Option 1: Personal Access Token (PAT) - Recommended

1. **Generate a token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name: "SLO Chatbot"
   - Select scopes: Check "repo" (full control of private repositories)
   - Click "Generate token"
   - **COPY THE TOKEN** (you won't see it again!)

2. **Push with token:**
   ```bash
   git push -u origin main
   ```
   - Username: Your GitHub username (harora-WM)
   - Password: Paste the token (not your password!)

### Option 2: SSH Key

1. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Enter passphrase (or press Enter for no passphrase)
   ```

2. **Add SSH key to GitHub:**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   # Copy the output
   ```
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste the key and save

3. **Change remote to SSH:**
   ```bash
   git remote set-url origin git@github.com:harora-WM/SLO_Chatbot_Our.git
   git push -u origin main
   ```

### Option 3: GitHub CLI (if installed)

```bash
gh auth login
git push -u origin main
```

---

## After Pushing

Your friend can clone with:

```bash
git clone https://github.com/harora-WM/SLO_Chatbot_Our.git
cd SLO_Chatbot_Our
```

Then they need to:
1. Copy `.env.example` to `.env`
2. Fill in their AWS and OpenSearch credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `streamlit run app.py`

---

## Current Status

✅ Git repository initialized
✅ All files committed (36 files, ~19,740 lines)
✅ Sensitive files (.env) properly excluded
✅ .env.example created for sharing
✅ Credentials moved from code to environment variables
⏳ Waiting for push to complete

Run the push command again after setting up authentication!
