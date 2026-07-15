# GitHub Setup & Deployment Guide

This guide helps you set up a private GitHub repository for the UTN International Collaboration Dashboard.

## Option 1: Create Private Repository on GitHub (Web Interface)

### Step 1: Create a New Repository

1. Go to [GitHub.com](https://github.com) and log in (create account if needed)
2. Click the **"+" icon** in the top right → **"New repository"**
3. Fill in the details:
   - **Repository name**: `utn-international-collaborations`
   - **Description**: `Dashboard for tracking international joint publications`
   - **Visibility**: Select **"Private"** ✓
   - **Initialize repository**: Leave unchecked (we'll push existing code)
4. Click **"Create repository"**

### Step 2: Push Code to GitHub (Windows Command Line)

Open PowerShell in the dashboard folder and run:

```powershell
# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: UTN International Collaboration Dashboard prototype"

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/utn-international-collaborations.git

# Rename branch to main (if needed)
git branch -M main

# Push code
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### Step 3: Invite Team Members (Optional)

1. Go to your repository on GitHub
2. Click **"Settings"** → **"Collaborators and teams"**
3. Click **"Add people"**
4. Enter email addresses of team members
5. Select permission level (Maintain, Write, or Read)

---

## Option 2: Quick Setup with GitHub CLI

If you have GitHub CLI installed:

```powershell
# Create private repository
gh repo create utn-international-collaborations --private --source=. --remote=origin --push

# Add team members
gh repo collaborators add USERNAME --permission maintain
```

---

## Repository Protection (Recommended)

To prevent accidental damage to main code:

1. Go to **Settings** → **Branches**
2. Click **"Add rule"** under "Branch protection rules"
3. Set **Branch name pattern**: `main`
4. Check:
   - ✓ Require pull request reviews before merging
   - ✓ Require status checks to pass
   - ✓ Include administrators
5. Click **"Create"**

---

## Access the Repository

Your repository URL will be:
```
https://github.com/YOUR_USERNAME/utn-international-collaborations
```

Team members can clone it:
```powershell
git clone https://github.com/YOUR_USERNAME/utn-international-collaborations.git
cd utn-international-collaborations
```

---

## Keeping the Repository Updated

After making changes locally:

```powershell
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

---

## Future: GitHub Actions (CI/CD)

When you're ready to add automated testing or deployment:

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Check syntax
        run: python -m py_compile app.py
```

---

## Migrating to React (Future)

When ready to rebuild as a React app:

1. Create a new branch: `git checkout -b feature/react-migration`
2. Build React frontend in `frontend/` folder
3. Keep Python backend in `backend/` folder
4. Create pull request for team review
5. Merge after approval

---

## Troubleshooting

### "Repository already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/utn-international-collaborations.git
git push -u origin main
```

### "Permission denied (publickey)"
Set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### "Authentication failed"
Use personal access token instead of password:
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Create new token with `repo` scope
3. Use token as password when pushing

---

## Support

- GitHub Docs: https://docs.github.com
- Git Tutorial: https://git-scm.com/book
- GitHub Learning Lab: https://lab.github.com

---

**Next Steps**: Once your GitHub repo is set up, you can:
1. Share the private link with your team
2. Collect feedback on the dashboard
3. Plan the React app conversion
4. Set up hosting (GitHub Pages, Vercel, or AWS)
