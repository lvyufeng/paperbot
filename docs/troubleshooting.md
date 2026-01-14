# Troubleshooting Guide

Common issues and solutions for PaperGen.

## Installation Issues

### Issue: pip install fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**
1. Update pip:
   ```bash
   pip install --upgrade pip
   ```

2. Check Python version:
   ```bash
   python --version  # Should be 3.10+
   ```

3. Try with explicit Python:
   ```bash
   python3.10 -m pip install -e .
   ```

---

### Issue: Module not found after installation

**Symptoms:**
```
ModuleNotFoundError: No module named 'papergen'
```

**Solutions:**
1. Ensure you're in the right directory:
   ```bash
   cd /path/to/academic-paper-pipeline
   pip install -e .
   ```

2. Check installation:
   ```bash
   pip list | grep papergen
   ```

3. Try reinstalling:
   ```bash
   pip uninstall papergen
   pip install -e .
   ```

---

## API Issues

### Issue: ANTHROPIC_API_KEY not found

**Symptoms:**
```
ValueError: ANTHROPIC_API_KEY not found in environment variables
```

**Solutions:**
1. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY='your-key-here'
   ```

2. Or create .env file:
   ```bash
   echo "ANTHROPIC_API_KEY=your-key-here" > .env
   ```

3. Verify it's set:
   ```bash
   echo $ANTHROPIC_API_KEY
   ```

4. For permanent setup (add to ~/.bashrc or ~/.zshrc):
   ```bash
   echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
   source ~/.bashrc
   ```

---

### Issue: API rate limit exceeded

**Symptoms:**
```
anthropic.RateLimitError: Rate limit exceeded
```

**Solutions:**
1. Wait a few minutes and retry
2. Draft sections one at a time instead of all:
   ```bash
   papergen draft draft-section introduction
   # Wait a bit
   papergen draft draft-section methods
   ```

3. Use lower tier operations:
   ```bash
   # Use Haiku model (faster, cheaper)
   papergen config api.model claude-3-haiku-20240307
   ```

---

### Issue: API timeout

**Symptoms:**
```
requests.exceptions.Timeout: Request timed out
```

**Solutions:**
1. Increase timeout:
   ```bash
   papergen config api.timeout 300
   ```

2. Check internet connection
3. Try again - might be temporary API issue

---

## Project Issues

### Issue: "Not in a papergen project directory"

**Symptoms:**
```
Error: Not in a papergen project directory.
```

**Solutions:**
1. Make sure you're in project directory:
   ```bash
   cd /path/to/your/paper/project
   ls -la .papergen  # Should exist
   ```

2. Initialize if needed:
   ```bash
   papergen init "Your Topic"
   ```

3. Check if .papergen exists:
   ```bash
   find . -name ".papergen" -type d
   ```

---

### Issue: Project already initialized

**Symptoms:**
```
Warning: Project already initialized in this directory.
```

**Solutions:**
1. If you want to start fresh, remove .papergen:
   ```bash
   rm -rf .papergen sources research outline drafts output
   papergen init "New Topic"
   ```

2. Or work with existing project:
   ```bash
   papergen status  # Check current state
   ```

---

## Research Issues

### Issue: PDF extraction fails

**Symptoms:**
```
Error extracting paper.pdf: ...
```

**Solutions:**
1. Check PDF is valid:
   ```bash
   file paper.pdf  # Should say "PDF document"
   ```

2. Try with different PDF:
   - Some PDFs are scanned images (need OCR)
   - Some are password protected
   - Some have corrupted metadata

3. Use text file instead:
   ```bash
   # Extract text manually and save as .txt
   papergen research add extracted_text.txt --source-type text
   ```

---

### Issue: No research sources found

**Symptoms:**
```
No research sources found. Add sources first...
```

**Solutions:**
1. Add sources:
   ```bash
   papergen research add paper.pdf
   ```

2. Check sources were added:
   ```bash
   papergen research list
   ```

3. Verify extraction:
   ```bash
   ls sources/extracted/*.json
   ```

---

## Outline Issues

### Issue: Outline generation fails

**Symptoms:**
```
Error generating outline: ...
```

**Solutions:**
1. Make sure research is organized:
   ```bash
   papergen research organize
   ls research/organized_notes.md  # Should exist
   ```

2. Try without AI first:
   ```bash
   papergen outline generate --no-use-ai
   ```

3. Then refine manually:
   ```bash
   # Edit outline/outline.md manually
   nano outline/outline.md
   ```

---

### Issue: Section not found in outline

**Symptoms:**
```
Error: Section 'methods' not found in outline.
Available sections: ...
```

**Solutions:**
1. Check available sections:
   ```bash
   papergen outline show
   ```

2. Use correct section ID (shown in list)

3. Or regenerate outline with that section:
   ```bash
   papergen outline generate --sections "intro,methods,results,conclusion"
   ```

---

## Drafting Issues

### Issue: Drafting takes too long

**Symptoms:**
- Command hangs or takes more than 2-3 minutes

**Solutions:**
1. Check API status: https://status.anthropic.com
2. Reduce content:
   - Limit research sources
   - Use shorter sections
3. Try one section at a time:
   ```bash
   papergen draft draft-section introduction
   ```

---

### Issue: Draft quality is poor

**Symptoms:**
- Generic content
- Missing details
- Incorrect information

**Solutions:**
1. Improve research organization:
   ```bash
   papergen research organize --focus "specific topics"
   ```

2. Refine outline with more specific objectives:
   ```bash
   papergen outline refine --interactive
   ```

3. Use guidance:
   ```bash
   papergen draft draft-section introduction \
     --guidance "Focus on recent 2024-2025 work and highlight novelty"
   ```

4. Revise with detailed feedback:
   ```bash
   papergen revise revise-section introduction \
     --feedback "Add specific examples and quantitative results. Cite Smith2024 and Jones2023."
   ```

---

### Issue: Citations not appearing

**Symptoms:**
- Draft has `[CITE:key]` markers
- No actual citations in output

**Solutions:**
1. Citations are placeholder markers - this is correct
2. They're replaced during formatting:
   ```bash
   papergen format latex  # Converts [CITE:key] to \cite{key}
   papergen format markdown  # Converts to (Author, Year)
   ```

3. To see formatted citations:
   ```bash
   papergen format preview --format latex
   ```

---

## Revision Issues

### Issue: Cannot revert - version not found

**Symptoms:**
```
Version X not found.
```

**Solutions:**
1. Check available versions:
   ```bash
   papergen revise history introduction
   ```

2. Revert to existing version:
   ```bash
   papergen revise revert introduction 1
   ```

---

### Issue: Revision doesn't improve content

**Symptoms:**
- Revisions make minimal changes
- Content quality doesn't improve

**Solutions:**
1. Be more specific with feedback:
   ```bash
   # Instead of: "improve this"
   # Use: "Add 3 specific examples of deep learning in climate prediction, citing recent papers"
   ```

2. Use focused polishing:
   ```bash
   papergen revise polish introduction --focus clarity
   papergen revise polish introduction --focus citations
   ```

3. Review and revise multiple times:
   ```bash
   papergen draft review introduction  # Get AI feedback first
   # Read the feedback, then:
   papergen revise revise-section introduction --feedback "[based on review]"
   ```

---

## Formatting Issues

### Issue: LaTeX compilation fails

**Symptoms:**
```
Compilation failed!
See full log: output/paper.log
```

**Solutions:**
1. Check if LaTeX is installed:
   ```bash
   pdflatex --version
   ```

2. Install LaTeX:
   - **macOS**: `brew install --cask mactex`
   - **Ubuntu**: `sudo apt-get install texlive-full`
   - **Windows**: Download MiKTeX from miktex.org

3. Check LaTeX log for errors:
   ```bash
   tail -50 output/paper.log
   ```

4. Common LaTeX errors:
   - Missing package: Install with LaTeX package manager
   - Special characters: Check for unescaped &, %, #, etc.

5. Try simpler template:
   ```bash
   papergen format latex --template custom
   ```

---

### Issue: PDF not generated

**Symptoms:**
- LaTeX file exists but no PDF
- Compilation seems to succeed but no PDF

**Solutions:**
1. Check for PDF:
   ```bash
   ls -lh output/paper.pdf
   ```

2. Run compilation twice (for references):
   ```bash
   papergen format compile
   papergen format compile
   ```

3. Check for compilation errors:
   ```bash
   cat output/paper.log | grep -i error
   ```

4. Try manual compilation:
   ```bash
   cd output
   pdflatex paper.tex
   pdflatex paper.tex
   ```

---

### Issue: Cannot open PDF

**Symptoms:**
```
Could not open PDF: ...
```

**Solutions:**
1. PDF viewer not installed:
   - **macOS**: Should work (uses Preview)
   - **Linux**: Install `xdg-open`
   - **Windows**: Should work (uses default PDF viewer)

2. Manual open:
   ```bash
   # macOS
   open output/paper.pdf

   # Linux
   xdg-open output/paper.pdf

   # Windows
   start output/paper.pdf
   ```

---

## Performance Issues

### Issue: Commands are slow

**Solutions:**
1. Use local operations when possible:
   ```bash
   papergen outline show  # Fast, no API
   papergen draft list    # Fast, no API
   papergen status        # Fast, no API
   ```

2. Batch operations:
   ```bash
   papergen draft all  # Better than drafting one by one
   ```

3. Use Haiku model (faster):
   ```bash
   papergen config api.model claude-3-haiku-20240307
   ```

---

### Issue: Disk space issues

**Symptoms:**
- Large project size
- Many version files

**Solutions:**
1. Check project size:
   ```bash
   du -sh .
   du -sh drafts/versions/
   ```

2. Clean old versions if needed:
   ```bash
   # Keep only last 3 versions
   cd drafts/versions/
   ls -t introduction_v*.md | tail -n +4 | xargs rm
   ```

3. Remove large source files:
   ```bash
   # After extraction, original PDFs can be moved elsewhere
   mv sources/pdfs/*.pdf ~/backup/
   ```

---

## Getting More Help

### Check Logs

```bash
# Check state file
cat .papergen/state.json

# Check configuration
cat .papergen/config.yaml

# Check source index
cat sources/extracted/index.json
```

### Debug Mode

```bash
# Run with verbose Python errors
python -m papergen.cli.main status
```

### Report Issues

If you find a bug:
1. Note the exact command you ran
2. Copy the error message
3. Check Python and package versions:
   ```bash
   python --version
   pip list | grep papergen
   ```

### Common Error Patterns

| Error | Likely Cause | Quick Fix |
|-------|--------------|-----------|
| `ModuleNotFoundError` | Not installed | `pip install -e .` |
| `ANTHROPIC_API_KEY not found` | API key not set | `export ANTHROPIC_API_KEY=...` |
| `Not in a papergen project` | Wrong directory | `cd` to project or `papergen init` |
| `No draft found` | Section not drafted | `papergen draft draft-section ...` |
| `LaTeX not found` | LaTeX not installed | Install LaTeX distribution |
| `Rate limit exceeded` | Too many API calls | Wait and retry |

### Best Practices to Avoid Issues

1. **Always check status**: `papergen status` before each stage
2. **One step at a time**: Don't skip stages in the pipeline
3. **Save API costs**: Test with small datasets first
4. **Version control**: Use git to track your project
5. **Backup**: Keep backups of important drafts
6. **Read output**: Pay attention to warnings and hints

### Still Stuck?

1. Re-read the [getting started guide](getting_started.md)
2. Check [command reference](commands.md)
3. Review [workflow examples](workflow.md)
4. Try starting a fresh project to isolate the issue
