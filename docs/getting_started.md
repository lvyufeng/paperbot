# Getting Started with PaperGen

This guide will walk you through creating your first academic paper with PaperGen.

## Prerequisites

1. **Python 3.10+** installed
2. **Anthropic API Key** (get one at https://console.anthropic.com/)
3. **(Optional) LaTeX distribution** for PDF compilation

## Installation

```bash
# Navigate to the project directory
cd /path/to/academic-paper-pipeline

# Install the package
pip install -e .

# Set up your API key
export ANTHROPIC_API_KEY='your-api-key-here'

# Or create a .env file
echo "ANTHROPIC_API_KEY=your-api-key" > .env
```

## Quick Start: Your First Paper

### Step 1: Initialize a Project

```bash
# Create a new directory for your paper
mkdir my-climate-paper
cd my-climate-paper

# Initialize the project
papergen init "Machine Learning for Climate Prediction" \
  --template ieee \
  --author "Your Name" \
  --keywords "machine learning, climate, prediction"
```

This creates the project structure:
```
my-climate-paper/
├── .papergen/          # Project configuration
├── sources/            # Research materials
├── research/           # Organized research
├── outline/            # Paper outline
├── drafts/             # Section drafts
└── output/             # Final paper
```

### Step 2: Add Research Sources

```bash
# Add PDF papers
papergen research add paper1.pdf paper2.pdf

# Add web sources
papergen research add --url https://arxiv.org/abs/2401.12345

# Add your notes
papergen research add notes.md --type notes

# List your sources
papergen research list
```

### Step 3: Organize Research with AI

```bash
# Let AI organize all your sources
papergen research organize

# Or focus on specific areas
papergen research organize --focus "methodology, results"

# View organized research
cat research/organized_notes.md
```

### Step 4: Generate Paper Outline

```bash
# Generate outline with AI
papergen outline generate

# Or specify sections
papergen outline generate --sections "intro,methods,results,conclusion"

# View the outline
papergen outline show

# Refine interactively if needed
papergen outline refine --interactive
```

### Step 5: Draft Sections

```bash
# Draft a single section
papergen draft draft-section introduction

# Or draft all sections at once
papergen draft all

# View a draft
papergen draft show introduction

# List all drafts
papergen draft list

# Check statistics
papergen draft stats
```

### Step 6: Review and Revise

```bash
# Get AI review of a section
papergen draft review introduction

# Revise based on feedback
papergen revise revise-section introduction \
  --feedback "Add more recent work from 2024-2025"

# Or revise all sections
papergen revise all --feedback "Strengthen academic tone"

# Polish for specific aspects
papergen revise polish introduction --focus clarity

# Compare versions
papergen revise compare introduction

# View version history
papergen revise history introduction
```

### Step 7: Format and Compile

```bash
# Generate LaTeX
papergen format latex

# Compile to PDF
papergen format compile

# Or compile and open
papergen format compile --open

# Generate Markdown version
papergen format markdown

# Check document statistics
papergen format stats
```

**Congratulations!** You've created your first academic paper with PaperGen! 🎉

## Next Steps

- Learn about [advanced features](workflow.md)
- Explore [all commands](commands.md)
- See [troubleshooting](troubleshooting.md) if you encounter issues
- Check [examples](examples.md) for more workflows

## Tips

1. **Save API costs**: Use `--no-use-ai` flag for testing without AI
2. **Iterative approach**: Draft, review, revise multiple times for best quality
3. **Version control**: All drafts maintain version history - experiment freely!
4. **Custom sections**: Not limited to standard sections - add custom ones to outline
5. **Multiple formats**: Generate both LaTeX and Markdown versions

## Common Workflow Patterns

### Pattern 1: Quick Draft
```bash
papergen init "Topic" --template ieee
papergen research add sources/*.pdf
papergen research organize
papergen outline generate
papergen draft all
papergen format latex
papergen format compile --open
```

### Pattern 2: Iterative Refinement
```bash
# Initial draft
papergen draft introduction

# Review and refine
papergen draft review introduction
papergen revise revise-section introduction --interactive

# Polish
papergen revise polish introduction --focus clarity
papergen revise polish introduction --focus citations

# Final check
papergen draft show introduction --format full
```

### Pattern 3: Section-by-Section
```bash
# Work on one section at a time
for section in introduction methods results conclusion; do
  papergen draft draft-section $section
  papergen draft review $section
  papergen revise revise-section $section --interactive
done

papergen format latex
```

## Project Status

Check your progress anytime:
```bash
papergen status
```

This shows:
- Current pipeline stage
- Completed stages with timestamps
- Statistics (sources, drafts, word count)

## Getting Help

```bash
# General help
papergen --help

# Command-specific help
papergen research --help
papergen draft --help
papergen format --help

# Subcommand help
papergen draft draft-section --help
```

## Need More Help?

- See the full [README](../README.md)
- Check [troubleshooting guide](troubleshooting.md)
- Review [workflow examples](workflow.md)
- Read [command reference](commands.md)
