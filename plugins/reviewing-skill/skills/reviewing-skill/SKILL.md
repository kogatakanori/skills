---
name: reviewing-skill
description: Reviews Agent Skills for compliance with Anthropic's official best practices. Use when the user asks to review a skill, check a skill for quality, validate skill compliance, or ensure a skill follows best practices. Analyzes SKILL.md structure, YAML frontmatter, content quality, progressive disclosure, workflows, and provides specific improvement recommendations.
---

# Reviewing Skills

Review Agent Skills for compliance with Anthropic's official best practices and provide actionable improvement recommendations.

## Quick Start

When asked to review a skill:

1. Read the skill's SKILL.md file
2. Follow the review workflow below
3. Use the checklist to ensure comprehensive coverage
4. Provide structured feedback with specific recommendations

## Review Workflow

Copy this checklist and track your progress:

```
Review Progress:
- [ ] Step 1: Read and analyze SKILL.md structure
- [ ] Step 2: Validate YAML frontmatter
- [ ] Step 3: Check content quality and organization
- [ ] Step 4: Review progressive disclosure patterns
- [ ] Step 5: Verify workflows and technical details
- [ ] Step 6: Generate improvement recommendations
```

### Step 1: Read and Analyze SKILL.md Structure

Read the entire SKILL.md file to understand:
- Overall structure and organization
- Presence of required sections
- File length (should be under 500 lines)
- Reference to bundled resources

**Check for:**
- Clear sections with headers
- Logical flow of information
- Appropriate use of examples
- Links to reference files (if any)

### Step 2: Validate YAML Frontmatter

Examine the YAML frontmatter for compliance:

**Name field requirements:**
- Maximum 64 characters
- Only lowercase letters, numbers, and hyphens
- No XML tags
- No reserved words: "anthropic", "claude"
- Uses gerund form (verb + -ing) or clear action-oriented naming
- Avoids vague names: `helper`, `utils`, `tools`

**Description field requirements:**
- Non-empty, maximum 1024 characters
- No XML tags
- Written in third person (not "I" or "you")
- Includes what the skill does AND when to use it
- Specific with key terms
- Avoids vague descriptions

**Good description example:**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**Common issues:**
- First person: "I can help you..." → "Processes..."
- Too vague: "Helps with documents" → Add specific capabilities and triggers
- Missing triggers: Add "Use when..." clause

### Step 3: Check Content Quality and Organization

Evaluate the SKILL.md body content:

**Conciseness:**
- Assumes Claude is smart - no explaining basic concepts
- Each paragraph justifies its token cost
- Prefers concise examples over verbose explanations
- No unnecessary background information

**Quality indicators:**
- Uses imperative/infinitive form for instructions
- Consistent terminology throughout
- Concrete examples, not abstract descriptions
- Clear, actionable steps
- No time-sensitive information (or properly marked as "old patterns")

**Appropriate degree of freedom:**
- High freedom: Multiple valid approaches, context-dependent decisions
- Medium freedom: Preferred pattern exists, some variation acceptable
- Low freedom: Fragile operations, consistency critical, specific sequence required

### Step 4: Review Progressive Disclosure Patterns

Check if the skill uses progressive disclosure effectively:

**File organization:**
- Reference files are one level deep from SKILL.md
- All reference files are linked from SKILL.md
- Clear description of when to read each reference
- No deeply nested references (SKILL.md → file1 → file2)

**Reference file best practices:**
- Files longer than 100 lines have table of contents
- Domain-specific content is separated
- Detailed information in references, not in SKILL.md

**Common patterns:**
- Pattern 1: High-level guide with references to detailed files
- Pattern 2: Domain-specific organization (separate files per domain)
- Pattern 3: Conditional details (advanced features in separate files)

**Path conventions:**
- All paths use forward slashes: `references/guide.md`
- No Windows-style backslashes: `references\guide.md`

### Step 5: Verify Workflows and Technical Details

**Workflow design (if applicable):**
- Complex tasks broken into clear steps
- Checklists provided for multi-step processes
- Each step is actionable
- Decision points clearly marked
- Feedback loops for validation

**Workflow checklist format:**
```markdown
Copy this checklist:

```
Task Progress:
- [ ] Step 1: Description
- [ ] Step 2: Description
```

**Step 1: Description**
Details and instructions...
```

**Technical details:**
- Required packages are listed with installation instructions
- No assumptions about pre-installed tools
- MCP tools use fully qualified names: `ServerName:tool_name`
- Scripts (if present) handle errors, don't punt to Claude

### Step 6: Generate Improvement Recommendations

Provide structured feedback using this format:

```markdown
## Skill Review Summary: [Skill Name]

### ✅ Strengths
- List what the skill does well
- Highlight best practices followed
- Note effective patterns used

### ⚠️ Issues Found

#### Critical (Must Fix)
- Issues that prevent skill from working
- Violations of required constraints
- Missing required fields

#### Important (Should Fix)
- Best practice violations
- Quality issues
- Performance concerns

#### Minor (Consider Fixing)
- Style inconsistencies
- Optimization opportunities
- Enhancement suggestions

### 📋 Specific Recommendations

1. **[Issue Category]**: [Specific problem]
   - Current: `[problematic code/text]`
   - Suggested: `[improved version]`
   - Reason: [why this matters]

2. **[Issue Category]**: [Specific problem]
   - Current: `[problematic code/text]`
   - Suggested: `[improved version]`
   - Reason: [why this matters]

### 📊 Compliance Score
- YAML Frontmatter: ✓/✗
- Content Quality: ✓/✗
- Progressive Disclosure: ✓/✗
- Workflows: ✓/✗
- Technical Details: ✓/✗
- **Overall: [Pass/Needs Work/Fail]**
```

## Reference Materials

**For comprehensive best practices**: See [best-practices.md](references/best-practices.md)

**For detailed checklist**: See [checklist.md](references/checklist.md)

Use these references to:
- Verify specific requirements
- Find examples of good vs bad patterns
- Understand the reasoning behind best practices
- Get detailed guidance on edge cases

## Common Issues and Quick Fixes

### Issue: Vague Description
```yaml
# Before
description: Helps with documents

# After
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

### Issue: First Person in Description
```yaml
# Before
description: I can help you process Excel files

# After
description: Processes Excel files and generates reports. Use when analyzing spreadsheets or .xlsx files.
```

### Issue: SKILL.md Too Long
```markdown
# In SKILL.md - Keep only essentials
## Quick start
Basic usage examples...

## Advanced features
**Form filling**: See [forms.md](references/forms.md)
**API reference**: See [reference.md](references/reference.md)
```

### Issue: Too Verbose
```markdown
# Before (150 tokens)
PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available...

# After (50 tokens)
Use pdfplumber for text extraction:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
```

### Issue: Windows Paths
```markdown
# Before
scripts\helper.py
references\guide.md

# After
scripts/helper.py
references/guide.md
```

### Issue: Multiple Options Without Default
```markdown
# Before
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image...

# After
Use pdfplumber for text extraction. For scanned PDFs requiring OCR, use pdf2image with pytesseract instead.
```

## Review Tips

**Be specific:** Instead of "improve description", say "add specific triggers like 'Use when working with PDF files'"

**Provide examples:** Show before/after for each recommendation

**Prioritize:** Separate critical issues from minor improvements

**Reference best practices:** Point to specific sections in best-practices.md when relevant

**Focus on impact:** Explain why each recommendation matters for skill effectiveness
