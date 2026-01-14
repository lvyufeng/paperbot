# PaperGen

AI-powered academic paper writing pipeline using Claude.

## Overview

PaperGen is a comprehensive tool for writing academic papers with AI assistance. It provides a modular pipeline that guides you from research organization through to final paper formatting.

### Key Features

- **Modular Pipeline**: Separate commands for research, outline, drafting, revision, and formatting
- **AI-Assisted**: Powered by Anthropic's Claude for intelligent content generation
- **Source Organization**: Extract and organize content from PDFs, web sources, and notes
- **Multiple Formats**: Output to LaTeX (IEEE, ACM, Springer templates) or Markdown
- **Citation Management**: Automatic citation handling and bibliography generation
- **Version Control**: Track revisions and maintain draft history

## Installation

### Requirements

- Python 3.10 or higher
- Anthropic API key (get one at https://console.anthropic.com/)

### Install

```bash
# Clone or download the repository
cd academic-paper-pipeline

# Install dependencies
pip install -e .

# Set up your API key
export ANTHROPIC_API_KEY='your-api-key-here'
# Or create a .env file (see .env.example)
```

## Quick Start

### Complete Example: Writing Your First Paper

Here's a complete workflow from start to finish:

```bash
# 1. Create a new paper project
mkdir my-climate-paper && cd my-climate-paper
papergen init "Machine Learning for Climate Prediction" \
  --template ieee \
  --author "Your Name" \
  --keywords "machine learning, climate, prediction"

# 2. Add your research sources
papergen research add ~/papers/climate/*.pdf
papergen research add --url https://arxiv.org/abs/2024.12345
papergen research add my_notes.md --source-type notes

# 3. Let AI organize your research
papergen research organize --focus "methodology, results, datasets"

# 4. Generate and refine the outline
papergen outline generate
papergen outline show  # Review the generated outline

# 5. Draft all sections
papergen draft all

# 6. Check your progress
papergen status
papergen draft stats

# 7. Review and revise key sections
papergen draft review introduction
papergen revise revise-section introduction --feedback "Add more recent 2024-2025 work"
papergen revise polish abstract --focus conciseness

# 8. Format and compile to PDF
papergen format latex --template ieee
papergen format compile --open

# Done! Your paper is ready.
```

### Step-by-Step Breakdown

#### 1. Initialize a Project

```bash
papergen init "Machine Learning for Climate Prediction" --template ieee --author "Your Name"
```

This creates a complete project structure with folders for sources, research, outlines, drafts, and output.

#### 2. Add Research Sources

```bash
# Add PDF papers
papergen research add paper1.pdf paper2.pdf paper3.pdf

# Add web sources (supports arXiv, academic sites)
papergen research add --url https://arxiv.org/abs/2024.12345

# Add your own notes and literature reviews
papergen research add notes.md --source-type notes

# List all sources
papergen research list
```

#### 3. Organize Research with AI

```bash
# AI analyzes and organizes all sources by themes, methods, and findings
papergen research organize

# Or focus on specific aspects
papergen research organize --focus "methodology, results, datasets"

# View organized research
cat research/organized_notes.md
```

#### 4. Generate Paper Outline

```bash
# Generate outline with AI (uses default academic structure)
papergen outline generate

# Or specify custom sections
papergen outline generate --sections "intro,background,methods,results,discussion,conclusion"

# View the outline
papergen outline show

# Refine interactively if needed
papergen outline refine --interactive
```

#### 5. Draft Sections

```bash
# Draft one section at a time
papergen draft draft-section introduction
papergen draft draft-section methods

# Or draft all sections at once (recommended)
papergen draft all

# View a draft
papergen draft show introduction
papergen draft show introduction --format full

# List all drafts
papergen draft list

# Check statistics
papergen draft stats
```

#### 6. Review and Revise

```bash
# Get AI review of a section
papergen draft review introduction

# Revise based on feedback
papergen revise revise-section introduction \
  --feedback "Add more recent work from 2024-2025 and strengthen the motivation"

# Revise all sections with same feedback
papergen revise all --feedback "Improve academic tone and add more citations"

# Polish specific aspects
papergen revise polish introduction --focus clarity
papergen revise polish methods --focus citations
papergen revise polish abstract --focus conciseness

# Compare versions
papergen revise compare introduction --version1 1 --version2 2

# View version history
papergen revise history introduction

# Revert if needed
papergen revise revert introduction 1
```

#### 7. Format and Compile

```bash
# Generate LaTeX with specific template
papergen format latex --template ieee
papergen format latex --template acm
papergen format latex --template springer

# Or generate Markdown
papergen format markdown --template standard
papergen format markdown --template arxiv

# Compile LaTeX to PDF (requires LaTeX installation)
papergen format compile

# Compile and automatically open PDF
papergen format compile --open

# Check document statistics
papergen format stats
```

## Workflow

```
papergen init → research add → research organize → outline generate
    → outline refine → draft → revise → format → compile
```

Each stage saves progress, so you can stop and resume anytime.

## Commands

### Project Management

- `papergen init <topic>` - Initialize new project
- `papergen status` - Show project status
- `papergen config [key] [value]` - View/modify configuration

### Research Stage

- `papergen research add <files>` - Add source materials
- `papergen research add --url <url>` - Add web source
- `papergen research organize` - Organize research with AI

### Outline Stage

- `papergen outline generate` - Generate paper outline
- `papergen outline refine` - Refine outline interactively

### Drafting Stage

- `papergen draft <section>` - Draft specific section
- `papergen draft all` - Draft all sections
- `papergen draft review <section>` - Review draft

### Revision Stage

- `papergen revise <section>` - Revise section with feedback
- `papergen revise all` - Revise all sections

### Formatting Stage

- `papergen format latex` - Generate LaTeX output
- `papergen format markdown` - Generate Markdown output
- `papergen compile` - Compile LaTeX to PDF

## Project Structure

When you run `papergen init`, it creates:

```
my-paper/
├── .papergen/           # Configuration and state
├── sources/             # Research materials
│   ├── pdfs/
│   ├── notes/
│   └── extracted/       # Extracted content (JSON)
├── research/            # Organized research
├── outline/             # Paper outline
├── drafts/              # Section drafts
└── output/              # Final output (LaTeX/PDF/Markdown)
```

## Configuration

Global configuration: `config/default_config.yaml`
Project configuration: `<project>/.papergen/config.yaml`

Key settings:
- AI model and parameters
- Word count targets per section
- Citation style (APA, IEEE, etc.)
- Template preferences

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
ruff check src/
```

## Documentation

For detailed guides and references, see the `docs/` directory:

- **[Getting Started Guide](docs/getting_started.md)** - Complete tutorial with examples
- **[Command Reference](docs/commands.md)** - Full documentation of all commands and options
- **[Workflow Examples](docs/workflow.md)** - 10 real-world workflow examples including:
  - Conference paper from PDFs
  - arXiv preprint from web sources
  - Quick blog post creation
  - Iterative refinement workflows
  - Collaborative workflows
  - Multi-format output
  - Emergency deadline workflows
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Solutions for common issues

## Tips for Best Results

1. **Quality Sources**: Add 5-10 high-quality papers for best AI-generated content
2. **Iterative Refinement**: Use multiple revision rounds for important sections
3. **Focus Areas**: Use `--focus` flag in research organization to emphasize specific topics
4. **Draft Guidance**: Provide specific `--guidance` when drafting sections for better results
5. **Polish Strategically**: Focus polish passes on critical sections (abstract, introduction, conclusion)
6. **Version Control**: Use git to track your project - all content is human-readable markdown
7. **Check Progress**: Run `papergen status` frequently to track pipeline progress

## Troubleshooting

### Quick Fixes

**API Key Issues:**
```bash
# Check if API key is set
echo $ANTHROPIC_API_KEY

# Or add to .env file
echo "ANTHROPIC_API_KEY=your-key" > .env

# For permanent setup (add to ~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

**Project Not Found:**
```bash
# Make sure you're in the project directory
cd /path/to/your/paper

# Check that .papergen exists
ls -la .papergen

# If not, initialize the project
papergen init "Your Topic"
```

**LaTeX Compilation Fails:**
```bash
# Check if LaTeX is installed
pdflatex --version

# Install LaTeX:
# macOS: brew install --cask mactex
# Ubuntu: sudo apt-get install texlive-full
# Windows: Download MiKTeX from miktex.org
```

**For more issues and solutions, see the [Troubleshooting Guide](docs/troubleshooting.md)**

## License

MIT License

## Support

For issues and feature requests, please visit the project repository.
