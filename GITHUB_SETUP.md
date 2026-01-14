# GitHub Setup Instructions

## Push PaperGen to GitHub Repository

Follow these steps to push your code to: `https://github.com/lvyufeng/paperbot.git`

### Step 1: Navigate to Your Project Directory

```bash
cd /storage/self/primary/Download/test
```

### Step 2: Initialize Git Repository

```bash
git init
```

### Step 3: Add All Files

```bash
git add .
```

### Step 4: Create Initial Commit

```bash
git commit -m "Initial commit: Complete PaperGen academic paper writing pipeline

- Phase 1: Foundation (CLI, state management, project structure)
- Phase 2: Research stage (PDF/web extraction, organization)
- Phase 3: AI integration (Claude API, prompts)
- Phase 4: Outline generation
- Phase 5: Drafting with citations
- Phase 6: Revision and version control
- Phase 7: LaTeX/Markdown formatting
- Phase 8: Documentation, logging, polish
- Complete documentation (LEARN.md, QUICKSTART.md, docs/)
- All 40+ commands implemented and tested"
```

### Step 5: Set Main Branch

```bash
git branch -M master
```

### Step 6: Add Remote Repository

```bash
git remote add origin https://github.com/lvyufeng/paperbot.git
```

### Step 7: Push to GitHub

```bash
git push -u origin master
```

---

## Complete Command Sequence (Copy & Paste)

```bash
cd /storage/self/primary/Download/test
git init
git add .
git commit -m "Initial commit: Complete PaperGen academic paper writing pipeline"
git branch -M master
git remote add origin https://github.com/lvyufeng/paperbot.git
git push -u origin master
```

---

## If Repository Already Exists

If the repository already has content, you may need to force push:

```bash
git push -u origin master --force
```

**Or** pull first and merge:

```bash
git pull origin master --allow-unrelated-histories
git push -u origin master
```

---

## Verify Upload

After pushing, verify at:
https://github.com/lvyufeng/paperbot

You should see:
- All source code in `src/papergen/`
- Documentation in `docs/`
- `README.md`, `LEARN.md`, `QUICKSTART.md`
- `pyproject.toml`, `setup.py`
- All configuration files

---

## Future Updates

After making changes:

```bash
git add .
git commit -m "Description of changes"
git push origin master
```

---

## Repository Structure on GitHub

```
paperbot/
├── src/papergen/              # Main source code
│   ├── cli/                   # Command-line interface
│   ├── core/                  # State, config, project management
│   ├── sources/               # PDF/web extraction
│   ├── ai/                    # Claude API integration
│   ├── document/              # Outline, drafting, citations
│   └── templates/             # LaTeX/Markdown builders
├── templates/                 # LaTeX templates
├── config/                    # Default configuration
├── docs/                      # Documentation
│   ├── getting_started.md
│   ├── commands.md
│   ├── workflow.md
│   └── troubleshooting.md
├── README.md                  # Main documentation
├── LEARN.md                   # Beginner's guide
├── QUICKSTART.md              # Quick reference
├── pyproject.toml             # Package configuration
├── setup.py                   # Installation script
├── .gitignore                 # Git ignore rules
└── .env.example               # Environment template
```

---

## Adding a GitHub README Badge (Optional)

After pushing, you can add badges to your README:

```markdown
# PaperGen (paperbot)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

AI-powered academic paper writing pipeline using Claude.
```

---

## Creating GitHub Release (Optional)

Create a release for v1.0.0:

1. Go to https://github.com/lvyufeng/paperbot/releases
2. Click "Create a new release"
3. Tag: `v1.0.0`
4. Title: `PaperGen v1.0.0 - Complete Academic Paper Writing Pipeline`
5. Description:
   ```
   Initial release of PaperGen - an AI-powered academic paper writing pipeline.

   Features:
   - Research organization from PDFs and web sources
   - AI-generated paper outlines
   - Automated section drafting with Claude
   - Iterative revision and version control
   - Multiple output formats (IEEE, ACM, Springer LaTeX + Markdown)
   - Citation management (APA, IEEE, ACM)
   - Comprehensive documentation

   See LEARN.md for complete beginner's guide.
   ```

---

## Need Help?

If you encounter issues:

1. **Authentication required**:
   ```bash
   # Use GitHub CLI or SSH
   gh auth login
   # Or set up SSH keys
   ```

2. **Permission denied**:
   - Make sure you're the repository owner
   - Check repository settings

3. **Merge conflicts**:
   ```bash
   git pull origin master
   # Resolve conflicts
   git add .
   git commit -m "Resolve conflicts"
   git push origin master
   ```

4. **Large files**:
   - Ensure no large test files are included
   - Check .gitignore is working
