# Learn PaperGen: Complete Beginner's Guide

Welcome! This guide will teach you everything you need to know to write academic papers with PaperGen and AI assistance.

## Table of Contents

1. [What is PaperGen?](#what-is-papergen)
2. [Installation](#installation)
3. [Your First Paper (Step by Step)](#your-first-paper-step-by-step)
4. [Understanding the Pipeline](#understanding-the-pipeline)
5. [Working with Research Sources](#working-with-research-sources)
6. [Creating Better Outlines](#creating-better-outlines)
7. [Drafting Techniques](#drafting-techniques)
8. [Revision Strategies](#revision-strategies)
9. [Formatting and Output](#formatting-and-output)
10. [Tips and Best Practices](#tips-and-best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Features](#advanced-features)

---

## What is PaperGen?

PaperGen is an AI-powered tool that helps you write academic papers from start to finish. Think of it as your research assistant that:

- **Organizes** your research papers and notes
- **Generates** paper outlines based on your research
- **Drafts** sections using AI (powered by Claude)
- **Revises** content iteratively to improve quality
- **Formats** your paper in LaTeX or Markdown
- **Compiles** to professional PDF documents

### How It Works

```
Your Research → AI Organization → Outline → AI Drafts → You Revise → Final Paper
```

The key insight: **You provide the research and direction; AI does the heavy lifting of writing.**

---

## Installation

### Step 1: Prerequisites

You need:
- **Python 3.10+** (check with `python --version`)
- **Anthropic API Key** (get free credits at https://console.anthropic.com/)
- **LaTeX** (optional, only for PDF compilation)

### Step 2: Install PaperGen

```bash
# Navigate to the PaperGen directory
cd /path/to/academic-paper-pipeline

# Install the package
pip install -e .

# Verify installation
papergen --help
```

### Step 3: Set Up API Key

PaperGen needs an API key to use Claude AI:

```bash
# Option 1: Environment variable (temporary)
export ANTHROPIC_API_KEY='your-key-here'

# Option 2: Create .env file (permanent)
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Option 3: Add to your shell config (permanent)
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

**Getting an API Key:**
1. Visit https://console.anthropic.com/
2. Sign up for an account
3. Go to API Keys section
4. Create a new key
5. Copy and paste it using one of the methods above

### Step 4: (Optional) Install LaTeX

For PDF compilation:

```bash
# macOS
brew install --cask mactex

# Ubuntu/Debian
sudo apt-get install texlive-full

# Windows
# Download and install MiKTeX from miktex.org
```

---

## Your First Paper (Step by Step)

Let's write a complete paper from scratch! We'll create a paper about "Machine Learning for Climate Prediction."

### Step 1: Create Project Directory

```bash
# Create a folder for your paper
mkdir my-climate-paper
cd my-climate-paper

# Initialize the project
papergen init "Machine Learning for Climate Prediction" \
  --template ieee \
  --author "Your Name" \
  --keywords "machine learning, climate, prediction"
```

**What just happened?**
- Created a project structure with folders for sources, research, outlines, drafts, and output
- Set up configuration files
- Initialized project state tracking

**Project structure created:**
```
my-climate-paper/
├── .papergen/          # Project configuration
├── sources/            # Your research files go here
├── research/           # AI-organized research
├── outline/            # Paper outline
├── drafts/             # Section drafts
└── output/             # Final paper
```

### Step 2: Add Your Research

Now add papers you want to reference. You can add PDFs, web sources, or your own notes.

```bash
# Add PDF papers from your computer
papergen research add ~/Downloads/paper1.pdf
papergen research add ~/Downloads/paper2.pdf
papergen research add ~/Downloads/paper3.pdf

# Add papers from the web (e.g., arXiv)
papergen research add --url https://arxiv.org/abs/2401.12345

# Add your own notes
echo "# My Research Notes

## Key Findings
- Finding 1: ML models improve climate predictions by 30%
- Finding 2: Deep learning works best for long-term forecasts

## Datasets
- ERA5 climate dataset
- CMIP6 model outputs
" > my_notes.md

papergen research add my_notes.md --source-type note

# See what you've added
papergen research list
```

**What's happening?**
- PaperGen extracts text, metadata, and citations from PDFs
- Web sources are fetched and processed
- Everything is saved in `sources/extracted/` as JSON files
- Your original files are kept in `sources/pdfs/` or `sources/notes/`

### Step 3: Organize Research with AI

Now let AI analyze and organize all your sources:

```bash
# Basic organization
papergen research organize

# Or focus on specific topics
papergen research organize --focus "methodology, results, datasets"

# View the organized research
cat research/organized_notes.md
```

**What AI does:**
- Reads all your sources
- Identifies common themes and concepts
- Extracts key methodologies and findings
- Groups related information
- Creates a structured summary

**This creates:** A file called `organized_notes.md` that summarizes your research in a way that's perfect for AI to draft from.

### Step 4: Generate Paper Outline

Let AI create a paper outline:

```bash
# Generate outline (uses standard academic structure)
papergen outline generate

# View the outline
papergen outline show
```

**The outline includes:**
- Abstract
- Introduction
- Related Work
- Methodology
- Results
- Discussion
- Conclusion

**Customize sections if needed:**
```bash
# Generate custom sections
papergen outline generate --sections "intro,background,methods,experiments,results,conclusion"
```

**Refine the outline interactively:**
```bash
papergen outline refine --interactive
```

### Step 5: Draft All Sections

Now the exciting part - AI writes your paper!

```bash
# Draft all sections at once (recommended)
papergen draft all

# This will take a few minutes...
# AI is writing each section based on:
# - Your research sources
# - The outline objectives
# - Academic writing standards
```

**What happens during drafting:**
1. AI reads your organized research
2. AI reads the outline objectives for each section
3. AI generates academic content with proper citations
4. Citations are added as `[CITE:key]` markers
5. Each section is saved in `drafts/`

**Check your progress:**
```bash
# List all drafted sections
papergen draft list

# View a specific section
papergen draft show introduction

# See the full content
papergen draft show introduction --format full

# Check statistics
papergen draft stats
```

### Step 6: Review and Improve

Let AI review its own work and then revise:

```bash
# Get AI review of a section
papergen draft review introduction

# The review will suggest improvements
# Now revise based on feedback
papergen revise revise-section introduction \
  --feedback "Add more recent work from 2024-2025 and strengthen motivation"

# Revise multiple sections with same feedback
papergen revise all --feedback "Add more quantitative results and strengthen citations"

# Polish for specific qualities
papergen revise polish abstract --focus conciseness
papergen revise polish introduction --focus clarity
papergen revise polish methods --focus citations
```

**Understanding revision:**
- `revise-section`: Major revision with specific feedback
- `polish`: Minor refinements (clarity, flow, citations, conciseness)
- Each revision creates a new version (version history preserved!)

**Compare versions:**
```bash
# See what changed between versions
papergen revise compare introduction --version1 1 --version2 2

# View all versions
papergen revise history introduction

# Go back to a previous version if needed
papergen revise revert introduction 1
```

### Step 7: Format and Compile

Turn your drafts into a professional paper:

```bash
# Generate LaTeX document
papergen format latex --template ieee

# Compile to PDF (requires LaTeX installation)
papergen format compile

# Compile and open the PDF
papergen format compile --open

# View the LaTeX source
cat output/paper.tex

# Check document stats
papergen format stats
```

**Available templates:**
- `ieee` - IEEE conference format
- `acm` - ACM conference format
- `springer` - Springer journal format

**Or generate Markdown instead:**
```bash
# Standard markdown
papergen format markdown

# arXiv format
papergen format markdown --template arxiv

# GitHub-friendly format
papergen format markdown --template github

# View the output
cat output/paper.md
```

### Step 8: Check Progress Anytime

```bash
# See overall project status
papergen status

# Shows:
# - Current stage
# - Completed stages
# - Statistics (sources, drafts, word count)
```

---

## Understanding the Pipeline

PaperGen follows a strict pipeline. Each stage must be completed before the next:

```
1. INIT      → Create project
2. RESEARCH  → Add and organize sources
3. OUTLINE   → Generate paper structure
4. DRAFT     → Write sections
5. REVISE    → Improve content
6. FORMAT    → Create final document
```

**Key Principle:** You can return to any stage and iterate!

```bash
# You can always:
papergen research add more_papers.pdf    # Add more sources
papergen outline refine                   # Improve outline
papergen draft draft-section intro       # Re-draft a section
papergen revise revise-section methods   # Revise again
papergen format latex --template acm     # Try different format
```

---

## Working with Research Sources

### Types of Sources

1. **PDF Papers** - Academic papers, reports
2. **Web Sources** - arXiv, academic websites
3. **Text Files** - Plain text or markdown
4. **Notes** - Your own research notes

### Adding Sources

```bash
# Single PDF
papergen research add paper.pdf

# Multiple PDFs
papergen research add paper1.pdf paper2.pdf paper3.pdf

# All PDFs in a directory
papergen research add papers/*.pdf

# From URL
papergen research add --url https://arxiv.org/abs/2024.12345

# Your notes (specify type)
papergen research add notes.md --source-type note
```

### What Gets Extracted

From PDFs:
- Full text content
- Title, authors, year
- Abstract
- Section headers
- Citations (if available)
- Figures and tables (metadata)

From web sources:
- Main content
- Metadata
- Links

### Organizing Research

The organization step is crucial - it determines the quality of your drafts!

```bash
# Basic organization (uses all sources)
papergen research organize

# Focus on specific aspects
papergen research organize --focus "methodology, datasets, results"
papergen research organize --focus "theoretical framework, limitations"
papergen research organize --focus "experimental setup, evaluation metrics"
```

**Pro Tips:**
- Add 5-10 high-quality papers for best results
- Include your own notes to guide the AI
- Use `--focus` to emphasize what matters for your paper
- Re-organize if you add more sources later

---

## Creating Better Outlines

The outline determines your paper's structure and content.

### Default Outline

```bash
papergen outline generate
```

Generates:
- Abstract
- Introduction
- Related Work
- Methodology
- Results
- Discussion
- Conclusion
- References

### Custom Sections

```bash
# Specify exactly what sections you want
papergen outline generate --sections "intro,background,methods,experiments,results,analysis,conclusion"
```

### Viewing the Outline

```bash
# See the full outline
papergen outline show
```

Shows for each section:
- Title
- Objectives
- Key points to cover
- Target word count
- Subsections

### Refining the Outline

The outline is editable! Two ways:

**1. Interactive refinement:**
```bash
papergen outline refine --interactive
```

**2. Manual editing:**
```bash
# Edit the outline directly
nano outline/outline.md

# The AI will use your edits when drafting
```

**What to adjust:**
- Section objectives (what the section should accomplish)
- Key points (specific things to include)
- Word count targets
- Subsection structure

---

## Drafting Techniques

### Basic Drafting

```bash
# Draft one section
papergen draft draft-section introduction

# Draft all sections
papergen draft all

# Draft specific sections only
papergen draft draft-section abstract
papergen draft draft-section introduction
papergen draft draft-section methods
```

### Using Guidance

Guide the AI's writing with the `--guidance` flag:

```bash
# Add specific instructions
papergen draft draft-section introduction \
  --guidance "Focus on the climate crisis urgency. Cite papers from 2023-2024. Emphasize the novelty of our approach."

papergen draft draft-section methods \
  --guidance "Use formal academic tone. Include mathematical notation for key algorithms. Provide pseudo-code."

papergen draft draft-section results \
  --guidance "Present results in order of importance. Include statistical significance tests. Refer to figures."
```

### Viewing Drafts

```bash
# Quick preview (first 500 characters)
papergen draft show introduction

# Full content
papergen draft show introduction --format full

# Raw markdown (for copying)
papergen draft show introduction --format markdown
```

### Draft Statistics

```bash
# Overall statistics
papergen draft stats

# Shows:
# - Sections drafted: 7
# - Total words: 4,523
# - Total citations: 23
# - Average words/section: 646
```

### Understanding Citations

AI adds citations as markers: `[CITE:smith2024]`

These are converted during formatting:
- **LaTeX:** `\cite{smith2024}`
- **Markdown:** `(Smith et al., 2024)`

Citations are stored in `research/citations.json` and `citations.bib`

---

## Revision Strategies

Revision is where your paper goes from good to great!

### Types of Revision

**1. Major Revision** - Significant changes based on feedback
```bash
papergen revise revise-section introduction \
  --feedback "Your detailed feedback here"
```

**2. Polish** - Minor refinements for specific qualities
```bash
papergen revise polish introduction --focus clarity
papergen revise polish introduction --focus flow
papergen revise polish introduction --focus citations
papergen revise polish introduction --focus conciseness
```

**3. Batch Revision** - Apply same feedback to all sections
```bash
papergen revise all --feedback "Strengthen academic tone and add more citations"
```

### Effective Feedback

❌ **Bad feedback:**
- "Make it better"
- "Improve this"
- "Fix the issues"

✅ **Good feedback:**
- "Add three specific examples of deep learning applications in climate science"
- "Strengthen the motivation by emphasizing the 2°C warming target and policy implications"
- "Add quantitative results with error bars and statistical significance tests"
- "Cite recent work from 2023-2024, especially Smith et al. and the IPCC AR6 report"
- "Reduce word count by 15% while keeping key information"

### Iterative Refinement

```bash
# Round 1: Get AI review
papergen draft review introduction

# Read the review, then revise
papergen revise revise-section introduction \
  --feedback "Add clearer motivation and state contributions upfront"

# Round 2: Polish for clarity
papergen revise polish introduction --focus clarity

# Round 3: Polish for citations
papergen revise polish introduction --focus citations

# Check the result
papergen draft show introduction --format full
```

### Version Management

Every revision creates a new version!

```bash
# See all versions
papergen revise history introduction

# Output:
# Version 1: Initial draft (2024-01-14 10:23)
# Version 2: Revision with feedback (2024-01-14 11:15)
# Version 3: Polished for clarity (2024-01-14 11:30)

# Compare two versions
papergen revise compare introduction --version1 1 --version2 3

# Go back if you don't like changes
papergen revise revert introduction 1
```

---

## Formatting and Output

### LaTeX Templates

```bash
# IEEE format (conferences)
papergen format latex --template ieee
papergen format compile --open

# ACM format (conferences)
papergen format latex --template acm
papergen format compile

# Springer format (journals)
papergen format latex --template springer
papergen format compile
```

**Output:** `output/paper.tex` and `output/paper.pdf`

### Markdown Output

```bash
# Standard markdown
papergen format markdown

# arXiv format (no table of contents)
papergen format markdown --template arxiv --no-toc

# GitHub format (with TOC)
papergen format markdown --template github
```

**Output:** `output/paper.md`

### Compilation

```bash
# Basic compilation
papergen format compile

# Open PDF after compiling
papergen format compile --open

# Use different LaTeX engine
papergen format compile --engine xelatex
papergen format compile --engine lualatex
```

**Note:** Compilation runs twice automatically to resolve references.

### Previewing

```bash
# Preview LaTeX (first 50 lines)
papergen format preview --format latex

# Preview Markdown
papergen format preview --format markdown

# Show more lines
papergen format preview --format latex --lines 100
```

### Multiple Formats

Generate both formats for different purposes:

```bash
# LaTeX for submission
papergen format latex --template ieee
papergen format compile

# Markdown for arXiv preprint
papergen format markdown --template arxiv

# Markdown for your blog
papergen format markdown --template github

# Now you have:
# - output/paper.pdf (for submission)
# - output/paper.md (for web)
```

---

## Tips and Best Practices

### Getting Started

1. **Start small** - Try with 3-5 papers first, see how it works
2. **Use good sources** - High-quality papers = high-quality drafts
3. **Add your own notes** - Guide the AI with your insights
4. **Check each stage** - Don't rush through; review outputs

### Research Phase

1. **Organize by theme** - Use `--focus` to emphasize what matters
2. **Include recent work** - Add 2023-2024 papers for current content
3. **Add your data** - Include your experimental notes, results
4. **Re-organize if needed** - Added more sources? Run organize again!

### Outline Phase

1. **Review the outline** - Use `papergen outline show` to check structure
2. **Customize sections** - Adjust to your paper's needs
3. **Set clear objectives** - Edit objectives in `outline/outline.md`
4. **Match conference requirements** - Adjust word counts, section names

### Drafting Phase

1. **Use guidance** - Tell AI specifically what you want
2. **Draft all at once** - Faster and more consistent
3. **Review statistics** - Check word counts against targets
4. **Don't expect perfection** - First draft is meant to be revised!

### Revision Phase

1. **Multiple rounds** - Plan for 2-3 revision rounds
2. **Specific feedback** - Give concrete, actionable feedback
3. **Focus on critical sections** - Spend most time on intro, conclusion
4. **Use polish for final touches** - After major revisions are done

### Formatting Phase

1. **Try different templates** - See which looks best
2. **Check citations** - Make sure they're all resolved
3. **Read the PDF** - Always review the compiled output
4. **Manual edits** - You can edit `drafts/*.md` directly if needed

### General Workflow

1. **Use git** - Track your project with version control
   ```bash
   git init
   git add .
   git commit -m "Initial draft"
   ```

2. **Check status frequently**
   ```bash
   papergen status
   ```

3. **Iterate freely** - Don't be afraid to re-draft, re-revise
   ```bash
   # You can always do this:
   papergen draft draft-section introduction  # Re-draft
   papergen revise revise-section methods    # Revise again
   papergen format latex --template acm      # Try new template
   ```

4. **Save API costs** - Use `--no-use-ai` for testing structure
   ```bash
   papergen outline generate --no-use-ai  # Creates basic template
   papergen research organize --no-use-ai # Simple concatenation
   ```

5. **Debug issues** - Use `--debug` flag to see what's happening
   ```bash
   papergen --debug draft all
   cat .papergen/papergen.log  # View detailed logs
   ```

---

## Troubleshooting

### Installation Issues

**Problem:** `pip install -e .` fails

```bash
# Solution 1: Update pip
pip install --upgrade pip

# Solution 2: Check Python version
python --version  # Should be 3.10+

# Solution 3: Use specific Python
python3.10 -m pip install -e .
```

### API Key Issues

**Problem:** `ANTHROPIC_API_KEY not found`

```bash
# Check if set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY='your-key'

# Or create .env file
echo "ANTHROPIC_API_KEY=your-key" > .env

# Verify it works
papergen status  # Should not error
```

**Problem:** API rate limit exceeded

```bash
# Solution: Wait a few minutes, then:
# Draft one section at a time instead of all
papergen draft draft-section introduction
# Wait a minute
papergen draft draft-section methods
# etc.
```

### Project Issues

**Problem:** "Not in a papergen project directory"

```bash
# Make sure you're in the project folder
cd /path/to/my-paper

# Check .papergen exists
ls -la .papergen

# If not, initialize
papergen init "Your Topic"
```

### PDF/LaTeX Issues

**Problem:** PDF extraction fails

```bash
# Some PDFs are scanned images or protected
# Solution: Extract text manually and use as .txt
papergen research add extracted_text.txt --source-type text
```

**Problem:** LaTeX compilation fails

```bash
# Check if LaTeX installed
pdflatex --version

# If not installed:
# macOS: brew install --cask mactex
# Ubuntu: sudo apt-get install texlive-full
# Windows: Download MiKTeX from miktex.org

# Check LaTeX log for errors
cat output/paper.log

# Try simpler template
papergen format latex --template custom
```

### Draft Quality Issues

**Problem:** Drafts are too generic

```bash
# Solution 1: Better research organization
papergen research organize --focus "specific topics"

# Solution 2: More specific outline
# Edit outline/outline.md and add detailed objectives

# Solution 3: Use guidance when drafting
papergen draft draft-section intro \
  --guidance "Focus on X, cite Y, emphasize Z"

# Solution 4: Revise with detailed feedback
papergen revise revise-section intro \
  --feedback "Add specific examples: [list examples]. Cite [papers]. Emphasize [points]."
```

**Problem:** Missing citations

```bash
# Citations are placeholders: [CITE:key]
# They're converted during formatting:
papergen format latex  # Converts to \cite{key}
papergen format markdown  # Converts to (Author, Year)

# To see formatted citations:
papergen format preview --format latex
```

### Getting Help

```bash
# General help
papergen --help

# Command-specific help
papergen research --help
papergen draft --help
papergen revise --help

# Subcommand help
papergen draft draft-section --help
papergen revise polish --help
```

---

## Advanced Features

### Custom Configuration

Edit `.papergen/config.yaml`:

```yaml
api:
  model: claude-opus-4-5
  temperature: 0.7
  max_tokens: 4096

content:
  default_word_counts:
    abstract: 250
    introduction: 800
    methods: 1200
    results: 1000
    conclusion: 600

citations:
  style: ieee  # or apa, acm
```

### Interactive Mode

Some commands support interactive mode:

```bash
# Interactive outline refinement
papergen outline refine --interactive

# Interactive revision
papergen revise revise-section intro --interactive
```

### Section-by-Section Deep Dive

Focus intensely on one section:

```bash
# Draft
papergen draft draft-section introduction

# Review
papergen draft review introduction

# Revise (round 1)
papergen revise revise-section introduction \
  --feedback "Strengthen motivation"

# Compare
papergen revise compare introduction

# Polish passes
papergen revise polish introduction --focus clarity
papergen revise polish introduction --focus flow
papergen revise polish introduction --focus citations
papergen revise polish introduction --focus conciseness

# Check history
papergen revise history introduction

# View final
papergen draft show introduction --format full

# If not satisfied, revert and try again
papergen revise revert introduction 1
papergen revise revise-section introduction \
  --feedback "New approach..."
```

### Collaborative Workflow

Use git for collaboration:

```bash
# Person A: Initial setup
git init
papergen init "Our Joint Research"
papergen research add sources/*.pdf
papergen research organize
git add -A
git commit -m "Add research sources"
git push

# Person B: Create outline
git pull
papergen outline generate
papergen outline refine --interactive
git add outline/
git commit -m "Add outline"
git push

# Person A: Draft intro and methods
git pull
papergen draft draft-section introduction
papergen draft draft-section methods
git add drafts/
git commit -m "Draft intro and methods"
git push

# Person B: Draft results and conclusion
git pull
papergen draft draft-section results
papergen draft draft-section conclusion
git add drafts/
git commit -m "Draft results and conclusion"
git push

# Person A: Format
git pull
papergen format latex
papergen format compile
git add output/
git commit -m "Generate final paper"
git push
```

### Manual Editing

You can always edit files directly:

```bash
# Edit outline
nano outline/outline.md

# Edit drafts
nano drafts/introduction.md

# After editing, format again
papergen format latex
papergen format compile
```

### Export Outline

```bash
# Export as Markdown
papergen outline export --format markdown

# Export as JSON
papergen outline export --format json
```

---

## Quick Reference

### Essential Commands

```bash
# Initialize
papergen init "Topic" --template ieee

# Add research
papergen research add *.pdf
papergen research organize

# Create outline
papergen outline generate
papergen outline show

# Draft
papergen draft all
papergen draft stats

# Revise
papergen draft review introduction
papergen revise revise-section introduction --feedback "..."
papergen revise polish abstract --focus conciseness

# Format
papergen format latex
papergen format compile --open

# Check status
papergen status
```

### Complete Workflow

```bash
# 1. Setup
mkdir my-paper && cd my-paper
papergen init "My Topic" --template ieee --author "Me"

# 2. Research
papergen research add papers/*.pdf
papergen research add notes.md --source-type note
papergen research organize --focus "methods, results"

# 3. Outline
papergen outline generate
papergen outline show

# 4. Draft
papergen draft all
papergen draft stats

# 5. Review & Revise
papergen draft review introduction
papergen revise revise-section introduction --feedback "Add recent work"
papergen revise polish abstract --focus conciseness

# 6. Format
papergen format latex --template ieee
papergen format compile --open

# Done!
```

---

## Next Steps

Now that you understand PaperGen, try:

1. **Write a real paper** - Pick a topic and follow the workflow
2. **Experiment with revision** - Try different feedback approaches
3. **Read the documentation** - Check `docs/` for detailed guides:
   - `docs/getting_started.md` - More examples
   - `docs/commands.md` - Complete command reference
   - `docs/workflow.md` - Real-world workflow examples
   - `docs/troubleshooting.md` - Detailed troubleshooting

4. **Share your experience** - What worked? What didn't?

---

## Summary

**Key Takeaways:**

1. PaperGen follows a pipeline: Research → Outline → Draft → Revise → Format
2. AI does the heavy lifting, but you guide it with feedback
3. Quality inputs = quality outputs (good sources, clear objectives)
4. Iteration is normal and encouraged (revise multiple times!)
5. Version history means you can experiment safely
6. Every stage can be revisited and improved

**Remember:** PaperGen is a tool to help you write faster, not to replace your expertise. You provide the research insight and direction; AI handles the tedious writing work.

**Happy paper writing! 🎓✨**
