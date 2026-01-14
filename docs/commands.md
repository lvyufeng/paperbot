# PaperGen Command Reference

Complete reference for all PaperGen commands.

## Global Commands

### `papergen init`

Initialize a new paper project.

```bash
papergen init "Paper Title" [OPTIONS]
```

**Arguments:**
- `topic` (required): Research topic or paper title

**Options:**
- `--template TEXT`: LaTeX template (ieee, acm, springer) [default: ieee]
- `--format TEXT`: Output format (latex, markdown) [default: latex]
- `--author TEXT`: Author name(s), comma-separated
- `--keywords TEXT`: Keywords, comma-separated
- `--path PATH`: Project path [default: current directory]

**Examples:**
```bash
# Basic initialization
papergen init "My Research Topic"

# With metadata
papergen init "ML for Climate" --template acm --author "John Doe, Jane Smith" --keywords "ML, climate"

# Custom location
papergen init "My Paper" --path /path/to/project
```

---

### `papergen status`

Show current project status.

```bash
papergen status
```

Displays:
- Project topic and configuration
- Pipeline stage progress
- Statistics (sources, drafts, etc.)

---

### `papergen config`

View or modify configuration.

```bash
papergen config [KEY] [VALUE] [OPTIONS]
```

**Options:**
- `--show`: Show all configuration

**Examples:**
```bash
# Show all config
papergen config --show

# Get a value
papergen config api.model

# Set a value
papergen config api.temperature 0.8
```

---

## Research Commands

### `papergen research add`

Add research sources to the project.

```bash
papergen research add FILES... [OPTIONS]
```

**Arguments:**
- `files`: One or more files to add

**Options:**
- `--url TEXT`: URL to add as source
- `--source-type TEXT`: Source type (pdf, text, note)

**Examples:**
```bash
# Add PDF files
papergen research add paper1.pdf paper2.pdf

# Add from URL
papergen research add --url https://arxiv.org/abs/2024.12345

# Add notes
papergen research add my_notes.md --source-type note

# Add directory of PDFs
papergen research add papers/*.pdf
```

---

### `papergen research organize`

Organize research sources using AI.

```bash
papergen research organize [OPTIONS]
```

**Options:**
- `--focus TEXT`: Focus areas (e.g., "methodology, results")
- `--use-ai / --no-use-ai`: Use AI for organization [default: true]

**Examples:**
```bash
# Basic organization
papergen research organize

# Focus on specific areas
papergen research organize --focus "methodology, datasets"

# Without AI (basic concatenation)
papergen research organize --no-use-ai
```

---

### `papergen research list`

List all research sources.

```bash
papergen research list
```

Shows:
- Source IDs
- Types (PDF, web, text)
- Titles
- Date added

---

## Outline Commands

### `papergen outline generate`

Generate paper outline from research.

```bash
papergen outline generate [OPTIONS]
```

**Options:**
- `--sections TEXT`: Comma-separated section names
- `--use-ai / --no-use-ai`: Use AI [default: true]

**Examples:**
```bash
# Default sections (abstract, intro, methods, results, discussion, conclusion)
papergen outline generate

# Custom sections
papergen outline generate --sections "intro,background,methods,results,conclusion"

# Without AI (basic template)
papergen outline generate --no-use-ai
```

---

### `papergen outline show`

Display the current outline.

```bash
papergen outline show
```

Shows:
- All sections with objectives
- Key points for each section
- Word count targets
- Subsections

---

### `papergen outline refine`

Refine the outline interactively.

```bash
papergen outline refine [OPTIONS]
```

**Options:**
- `--section TEXT`: Specific section to refine
- `--interactive / --no-interactive`: Interactive mode [default: true]

**Examples:**
```bash
# Refine all sections interactively
papergen outline refine --interactive

# Refine specific section
papergen outline refine --section introduction
```

---

### `papergen outline export`

Export outline to file.

```bash
papergen outline export [OPTIONS]
```

**Options:**
- `--format TEXT`: Export format (markdown, json) [default: markdown]

**Examples:**
```bash
# Export as Markdown
papergen outline export --format markdown

# Export as JSON
papergen outline export --format json
```

---

## Draft Commands

### `papergen draft draft-section`

Draft a specific section.

```bash
papergen draft draft-section SECTION [OPTIONS]
```

**Arguments:**
- `section` (required): Section ID (e.g., "introduction")

**Options:**
- `--guidance TEXT`: Additional guidance for drafting
- `--use-ai / --no-use-ai`: Use AI [default: true]

**Examples:**
```bash
# Basic drafting
papergen draft draft-section introduction

# With guidance
papergen draft draft-section methods --guidance "Focus on statistical methods"

# Available sections from outline
papergen outline show  # to see section IDs
```

---

### `papergen draft all`

Draft all sections at once.

```bash
papergen draft all [OPTIONS]
```

**Options:**
- `--skip-existing / --no-skip-existing`: Skip already drafted sections [default: true]
- `--use-ai / --no-use-ai`: Use AI [default: true]

**Examples:**
```bash
# Draft all sections
papergen draft all

# Re-draft everything
papergen draft all --no-skip-existing
```

---

### `papergen draft show`

Show a drafted section.

```bash
papergen draft show SECTION [OPTIONS]
```

**Arguments:**
- `section` (required): Section ID

**Options:**
- `--format TEXT`: Output format (preview, full, markdown) [default: preview]

**Examples:**
```bash
# Preview (first 500 chars)
papergen draft show introduction

# Full content
papergen draft show introduction --format full

# Raw markdown
papergen draft show introduction --format markdown
```

---

### `papergen draft review`

Get AI review of a drafted section.

```bash
papergen draft review SECTION
```

**Arguments:**
- `section` (required): Section ID

**Examples:**
```bash
papergen draft review introduction
```

---

### `papergen draft list`

List all drafted sections.

```bash
papergen draft list
```

Shows:
- Section IDs and titles
- Word counts
- Citation counts
- Version numbers

---

### `papergen draft stats`

Show drafting statistics.

```bash
papergen draft stats
```

Displays:
- Total sections drafted
- Total word count
- Total citations
- Average words per section

---

## Revise Commands

### `papergen revise revise-section`

Revise a section based on feedback.

```bash
papergen revise revise-section SECTION [OPTIONS]
```

**Arguments:**
- `section` (required): Section ID

**Options:**
- `--feedback TEXT`: Feedback for revision
- `--interactive`: Interactive mode with prompts
- `--use-ai / --no-use-ai`: Use AI [default: true]

**Examples:**
```bash
# With direct feedback
papergen revise revise-section introduction --feedback "Add more recent work from 2024-2025"

# Interactive mode
papergen revise revise-section methods --interactive

# Multiple revisions
papergen revise revise-section introduction --feedback "First round"
papergen revise revise-section introduction --feedback "Second round"
```

---

### `papergen revise all`

Revise all sections with same feedback.

```bash
papergen revise all --feedback TEXT [OPTIONS]
```

**Options:**
- `--feedback TEXT` (required): Feedback to apply
- `--skip-sections TEXT`: Comma-separated sections to skip
- `--use-ai / --no-use-ai`: Use AI [default: true]

**Examples:**
```bash
# Revise all
papergen revise all --feedback "Strengthen academic tone and add citations"

# Skip abstract
papergen revise all --feedback "Make more concise" --skip-sections "abstract"
```

---

### `papergen revise compare`

Compare different versions of a section.

```bash
papergen revise compare SECTION [OPTIONS]
```

**Arguments:**
- `section` (required): Section ID

**Options:**
- `--version1 INTEGER`: First version number
- `--version2 INTEGER`: Second version number

**Examples:**
```bash
# Compare previous and current
papergen revise compare introduction

# Compare specific versions
papergen revise compare introduction --version1 1 --version2 3
```

---

### `papergen revise revert`

Revert section to a previous version.

```bash
papergen revise revert SECTION VERSION
```

**Arguments:**
- `section` (required): Section ID
- `version` (required): Version number to revert to

**Examples:**
```bash
# Revert to version 1
papergen revise revert introduction 1
```

---

### `papergen revise history`

Show version history for a section.

```bash
papergen revise history SECTION
```

**Arguments:**
- `section` (required): Section ID

**Examples:**
```bash
papergen revise history introduction
```

---

### `papergen revise polish`

Polish a section (focused refinement).

```bash
papergen revise polish SECTION [OPTIONS]
```

**Arguments:**
- `section` (required): Section ID

**Options:**
- `--focus TEXT`: Focus area (clarity, flow, citations, conciseness)
- `--use-ai / --no-use-ai`: Use AI [default: true]

**Examples:**
```bash
# General polish
papergen revise polish introduction

# Focus on clarity
papergen revise polish introduction --focus clarity

# Focus on citations
papergen revise polish methods --focus citations

# Multiple polish passes
papergen revise polish introduction --focus clarity
papergen revise polish introduction --focus flow
papergen revise polish introduction --focus citations
```

---

## Format Commands

### `papergen format latex`

Generate LaTeX document from drafts.

```bash
papergen format latex [OPTIONS]
```

**Options:**
- `--template TEXT`: Template name (ieee, acm, springer)
- `--output PATH`: Output file path

**Examples:**
```bash
# Default (uses project template)
papergen format latex

# Specific template
papergen format latex --template acm

# Custom output
papergen format latex --output /path/to/custom.tex
```

---

### `papergen format markdown`

Generate Markdown document from drafts.

```bash
papergen format markdown [OPTIONS]
```

**Options:**
- `--template TEXT`: Template (standard, arxiv, github) [default: standard]
- `--output PATH`: Output file path
- `--toc / --no-toc`: Include table of contents [default: true]

**Examples:**
```bash
# Standard markdown
papergen format markdown

# arXiv format
papergen format markdown --template arxiv --no-toc

# GitHub format with custom output
papergen format markdown --template github --output README.md
```

---

### `papergen format compile`

Compile LaTeX to PDF.

```bash
papergen format compile [OPTIONS]
```

**Options:**
- `--source PATH`: LaTeX source file
- `--open`: Open PDF after compilation
- `--engine TEXT`: LaTeX engine (pdflatex, xelatex, lualatex) [default: pdflatex]

**Examples:**
```bash
# Basic compilation
papergen format compile

# Compile and open
papergen format compile --open

# Use XeLaTeX
papergen format compile --engine xelatex

# Custom source
papergen format compile --source custom.tex
```

**Requirements:**
- LaTeX distribution must be installed
- macOS: `brew install --cask mactex`
- Ubuntu: `sudo apt-get install texlive-full`
- Windows: Download MiKTeX from miktex.org

---

### `papergen format preview`

Preview output without saving.

```bash
papergen format preview [OPTIONS]
```

**Options:**
- `--format TEXT`: Format to preview (latex, markdown) [default: latex]
- `--lines INTEGER`: Number of lines to show [default: 50]

**Examples:**
```bash
# Preview LaTeX
papergen format preview --format latex --lines 30

# Preview Markdown
papergen format preview --format markdown
```

---

### `papergen format stats`

Show document statistics.

```bash
papergen format stats
```

Displays:
- Section count
- Word count
- Citation count
- Output files (if generated)

---

## Tips and Tricks

### Pipeline Order
Always follow this order:
1. `init` → 2. `research` → 3. `outline` → 4. `draft` → 5. `revise` → 6. `format`

### Quick Commands
```bash
# Full pipeline in one go
papergen init "Topic" && \
  papergen research add *.pdf && \
  papergen research organize && \
  papergen outline generate && \
  papergen draft all && \
  papergen format latex && \
  papergen format compile --open
```

### Check Progress
```bash
# Quick status check
papergen status

# Detailed stats
papergen draft stats
papergen format stats
```

### Error Recovery
```bash
# If drafting fails, try individual sections
papergen draft draft-section introduction
papergen draft draft-section methods
# etc.

# If revision goes wrong, check history and revert
papergen revise history introduction
papergen revise revert introduction 1
```

### Save API Costs
```bash
# Use --no-use-ai for testing structure
papergen outline generate --no-use-ai
papergen research organize --no-use-ai
```

### Multiple Formats
```bash
# Generate both formats
papergen format latex
papergen format markdown

# Now you have paper.tex and paper.md
```
