# Workflow Examples

Real-world workflows for different use cases.

## Example 1: Conference Paper from PDFs

**Scenario**: You have 10 PDF papers and need to write an IEEE conference paper.

```bash
# 1. Setup
mkdir my-conference-paper
cd my-conference-paper
papergen init "Deep Learning for Medical Image Analysis" \
  --template ieee \
  --author "Jane Doe, John Smith" \
  --keywords "deep learning, medical imaging, diagnosis"

# 2. Add all PDFs
papergen research add ~/research/papers/*.pdf

# Verify addition
papergen research list

# 3. Organize research focusing on methods and results
papergen research organize --focus "methodology, results, datasets"

# Review organized research
cat research/organized_notes.md

# 4. Generate outline
papergen outline generate

# Review and refine
papergen outline show
papergen outline refine --interactive

# 5. Draft all sections
papergen draft all

# Check progress
papergen draft stats

# 6. Review each section
for section in abstract introduction methods results discussion conclusion; do
  echo "=== Reviewing $section ==="
  papergen draft review $section
done

# 7. Revise based on reviews
papergen revise all --feedback "Strengthen methodology description and add more quantitative results"

# 8. Polish key sections
papergen revise polish abstract --focus conciseness
papergen revise polish introduction --focus clarity
papergen revise polish methods --focus citations

# 9. Format and compile
papergen format latex --template ieee
papergen format compile --open

# Done! Your paper is ready for submission.
```

---

## Example 2: arXiv Preprint from Web Sources

**Scenario**: Creating a survey paper primarily from arXiv papers and online resources.

```bash
# 1. Initialize
papergen init "Survey of Transformer Architectures" \
  --template custom \
  --format markdown

# 2. Add web sources
papergen research add --url https://arxiv.org/abs/1706.03762  # Original transformer
papergen research add --url https://arxiv.org/abs/1810.04805  # BERT
papergen research add --url https://arxiv.org/abs/2005.14165  # GPT-3
papergen research add --url https://arxiv.org/abs/2104.09864  # ViT
# ... add more

# Also add your literature review notes
papergen research add literature_review.md --source-type notes

# 3. Organize
papergen research organize --focus "architecture, performance, applications"

# 4. Custom outline for survey paper
papergen outline generate --sections "abstract,introduction,background,transformers,variants,applications,challenges,conclusion"

# 5. Draft incrementally (survey papers are long)
papergen draft draft-section abstract
papergen draft draft-section introduction
papergen draft draft-section background
# ... continue

# Review as you go
papergen draft review introduction
papergen revise revise-section introduction --interactive

# 6. Format as Markdown for arXiv
papergen format markdown --template arxiv --no-toc

# Upload paper.md to arXiv
cat output/paper.md
```

---

## Example 3: Quick Blog Post / Technical Report

**Scenario**: Turning research into a blog post or internal technical report.

```bash
# 1. Quick setup
papergen init "Understanding Neural Network Optimization" \
  --template custom \
  --format markdown \
  --author "Your Name"

# 2. Add your notes and a few key papers
papergen research add my_notes.md
papergen research add paper1.pdf paper2.pdf

# 3. Simple organization
papergen research organize

# 4. Short-form outline
papergen outline generate --sections "intro,background,main-concepts,examples,conclusion"

# 5. Draft with specific style
papergen draft draft-section intro \
  --guidance "Write in a conversational, blog-friendly style. Use simple language and examples."

papergen draft all

# 6. Polish for readability
papergen revise polish intro --focus clarity
papergen revise polish main-concepts --focus clarity

# 7. Export as Markdown for blog
papergen format markdown --template github --output blog_post.md

# Now you can publish to Medium, your blog, etc.
```

---

## Example 4: Iterative Refinement Workflow

**Scenario**: High-stakes paper that needs multiple rounds of refinement.

```bash
# Setup (already done)
cd my-important-paper

# === Round 1: Initial Draft ===
papergen draft all
papergen draft stats

# === Round 2: AI Review ===
echo "=== Round 2: AI Reviews ==="
for section in introduction methods results conclusion; do
  papergen draft review $section > reviews/$section-review-r1.md
done

# Read reviews, then revise
papergen revise revise-section introduction --feedback "Add clearer motivation and state contributions upfront"
papergen revise revise-section methods --feedback "Add algorithm pseudo-code and complexity analysis"
papergen revise revise-section results --feedback "Add statistical significance tests and error bars"

# === Round 3: Focus on Clarity ===
echo "=== Round 3: Clarity Pass ==="
for section in introduction methods results conclusion; do
  papergen revise polish $section --focus clarity
done

# === Round 4: Citation Pass ===
echo "=== Round 4: Citation Pass ==="
for section in introduction methods results; do
  papergen revise polish $section --focus citations
done

# === Round 5: Conciseness ===
echo "=== Round 5: Make Concise ==="
papergen revise all --feedback "Reduce word count by 15% while keeping key information"

# Check word counts
papergen draft stats

# === Final: Format and Review ===
papergen format latex
papergen format compile

# Compare versions to see progress
papergen revise compare introduction --version1 1 --version2 5
```

---

## Example 5: Collaborative Workflow

**Scenario**: Multiple people working on the same paper.

```bash
# Person A: Initial setup and research
git init
git add .gitignore README.md
git commit -m "Initial commit"

papergen init "Our Joint Research Project"
papergen research add sources/*.pdf
papergen research organize
git add -A
git commit -m "Add research sources and organization"
git push

# Person B: Create outline
git pull
papergen outline generate
papergen outline refine --interactive
git add outline/
git commit -m "Add paper outline"
git push

# Person A: Draft introduction and methods
git pull
papergen draft draft-section introduction
papergen draft draft-section methods
git add drafts/introduction.* drafts/methods.*
git commit -m "Draft introduction and methods"
git push

# Person B: Draft results and conclusion
git pull
papergen draft draft-section results
papergen draft draft-section conclusion
git add drafts/results.* drafts/conclusion.*
git commit -m "Draft results and conclusion"
git push

# Person A: Review and revise all
git pull
papergen revise all --feedback "First round revisions"
git add drafts/
git commit -m "First revision pass"
git push

# Person B: Format and compile
git pull
papergen format latex
papergen format compile
git add output/
git commit -m "Generate final paper"
git push

# Review together
papergen status
papergen format stats
```

---

## Example 6: Multi-Format Output

**Scenario**: Need both LaTeX for conference and Markdown for blog/website.

```bash
# After drafting is complete...

# 1. Generate conference version (LaTeX)
papergen format latex --template acm --output output/conference.tex
papergen format compile --source output/conference.tex

# 2. Generate blog version (Markdown)
papergen format markdown --template github --output output/blog_post.md

# 3. Generate arXiv version (Markdown)
papergen format markdown --template arxiv --no-toc --output output/arxiv.md

# Now you have:
# - conference.pdf for ACM submission
# - blog_post.md for your website
# - arxiv.md for arXiv preprint
```

---

## Example 7: Emergency Deadline Workflow

**Scenario**: Paper due in 24 hours, need to work fast.

```bash
# 0. Setup (5 minutes)
papergen init "Emergency Paper" --template ieee
papergen research add critical_papers/*.pdf  # Only the most important papers
papergen research organize

# 1. Fast outline (10 minutes)
papergen outline generate --no-use-ai  # Faster, then manually edit
nano outline/outline.md  # Quick manual refinement

# 2. Parallel drafting (2 hours)
# Draft all at once to save time
papergen draft all

# 3. Quick review (30 minutes)
# Only review key sections
papergen draft review introduction
papergen draft review results

# 4. Targeted revisions (1 hour)
# Focus on critical issues only
papergen revise revise-section introduction --feedback "Strengthen motivation"
papergen revise revise-section results --feedback "Add statistical tests"

# 5. Quick polish (30 minutes)
# Polish critical sections only
papergen revise polish abstract --focus conciseness
papergen revise polish introduction --focus clarity

# 6. Format and compile (15 minutes)
papergen format latex
papergen format compile --open

# 7. Manual final check
# Read through output/paper.pdf
# Make any manual edits to drafts/*.md
# Re-format if needed:
# papergen format latex && papergen format compile

# Total: ~4-5 hours for full draft
```

---

## Example 8: Section-by-Section Deep Dive

**Scenario**: Working on one section at a time with maximum quality.

```bash
# Focus on Introduction
echo "=== Working on Introduction ==="

# 1. Draft
papergen draft draft-section introduction

# 2. Review
papergen draft review introduction > intro_review.md
cat intro_review.md

# 3. First revision based on review
papergen revise revise-section introduction \
  --feedback "$(cat intro_review.md | grep 'Suggestions' -A 10)"

# 4. Compare versions
papergen revise compare introduction

# 5. Polish passes
papergen revise polish introduction --focus clarity
papergen revise polish introduction --focus flow
papergen revise polish introduction --focus citations
papergen revise polish introduction --focus conciseness

# 6. Check version history
papergen revise history introduction

# 7. View final result
papergen draft show introduction --format full

# 8. If not satisfied, revert and try again
papergen revise revert introduction 2
papergen revise revise-section introduction --feedback "New approach..."

# Repeat for each section...
```

---

## Example 9: Using Custom Research Notes

**Scenario**: You have extensive personal notes and want to incorporate them.

```bash
# 1. Organize your notes into markdown files
cat > sources/notes/methodology_notes.md << EOF
# Methodology Notes

## Data Collection
- Used dataset X with Y samples
- Preprocessing steps: ...

## Model Architecture
- Based on transformer architecture
- Modified with custom attention mechanism
EOF

cat > sources/notes/results_notes.md << EOF
# Results Notes

## Main Findings
- Achieved 95% accuracy
- Outperformed baseline by 10%
- Statistical significance: p < 0.01
EOF

# 2. Add all notes
papergen research add sources/notes/*.md --source-type notes

# 3. Also add supporting papers
papergen research add papers/*.pdf

# 4. Organize everything together
papergen research organize

# 5. The AI will now use both your notes and papers
papergen outline generate
papergen draft all

# Your personal notes and insights are incorporated!
```

---

## Example 10: Recovering from Mistakes

**Scenario**: Something went wrong, need to recover.

```bash
# Problem: Drafted all sections but they're not good

# Solution 1: Revert to earlier versions
for section in introduction methods results; do
  papergen revise history $section  # Check versions
  papergen revise revert $section 1  # Revert to v1
done

# Solution 2: Improve research organization
papergen research organize --focus "specific topics"

# Solution 3: Refine outline
papergen outline refine --interactive

# Solution 4: Re-draft with better guidance
papergen draft draft-section introduction \
  --guidance "Focus on X, Y, Z. Use formal academic tone. Cite recent 2024 work."

# Problem: Lost work

# Solution: Everything is saved!
ls drafts/versions/  # All versions preserved
ls drafts/*.json     # Metadata preserved
cat .papergen/state.json  # Project state preserved

# Worst case: Start from backups
cp -r project_backup/.papergen .
cp -r project_backup/drafts .
papergen status
```

---

## Tips for All Workflows

1. **Check status frequently**: `papergen status`
2. **Save intermediate results**: Commit to git regularly
3. **Use version history**: Don't fear experimentation
4. **Iterate**: Multiple revision rounds improve quality
5. **Focus**: Polish critical sections (intro, conclusion) more
6. **Preview**: Check output before final compile
7. **Manual editing**: You can always edit drafts/*.md directly
8. **Backup**: Keep backups of important work

## Next Steps

- Review [command reference](commands.md) for all options
- Check [troubleshooting](troubleshooting.md) if issues arise
- Read [getting started](getting_started.md) for basics
