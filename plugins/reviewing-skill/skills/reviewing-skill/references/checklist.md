# Skill Review Checklist

Use this checklist when reviewing Skills for quality and best practices compliance.

## 1. YAML Frontmatter

### Name Field
- [ ] Name is present and non-empty
- [ ] Maximum 64 characters
- [ ] Contains only lowercase letters, numbers, and hyphens
- [ ] Does not contain XML tags
- [ ] Does not contain reserved words: "anthropic", "claude"
- [ ] Uses gerund form (verb + -ing) or clear action-oriented naming
- [ ] Avoids vague names: `helper`, `utils`, `tools`
- [ ] Avoids overly generic names: `documents`, `data`, `files`
- [ ] Name is consistent with skill collection patterns

### Description Field
- [ ] Description is present and non-empty
- [ ] Maximum 1024 characters
- [ ] Does not contain XML tags
- [ ] Written in third person (not "I" or "you")
- [ ] Includes what the Skill does
- [ ] Includes when to use it (specific triggers/contexts)
- [ ] Specific and includes key terms
- [ ] Avoids vague descriptions

**Good description example:**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**Bad description examples:**
```yaml
description: Helps with documents  # Too vague
description: I can help you process Excel files  # First person
```

## 2. SKILL.md Body Structure

### Length and Organization
- [ ] SKILL.md body is under 500 lines
- [ ] If over 500 lines, content is split into reference files
- [ ] Clear sections with headers
- [ ] Logical flow of information
- [ ] No duplicate content between SKILL.md and reference files

### Content Quality
- [ ] Concise - assumes Claude is smart
- [ ] No unnecessary explanations
- [ ] Examples are concrete, not abstract
- [ ] Instructions are clear and actionable
- [ ] Appropriate degree of freedom (high/medium/low)
- [ ] No time-sensitive information (or properly marked as old patterns)
- [ ] Consistent terminology throughout

**Conciseness check:**
- [ ] Each paragraph justifies its token cost
- [ ] No explaining basic concepts Claude already knows
- [ ] Prefer concise examples over verbose explanations

### Instructions Format
- [ ] Uses imperative/infinitive form
- [ ] Clear action verbs
- [ ] Step-by-step when appropriate
- [ ] Includes decision points when needed

## 3. Progressive Disclosure

### File Organization
- [ ] Reference files are one level deep from SKILL.md
- [ ] All reference files are linked from SKILL.md
- [ ] Clear description of when to read each reference file
- [ ] No deeply nested references (SKILL.md → file1 → file2)

### Reference Files
- [ ] Reference files longer than 100 lines have table of contents
- [ ] Domain-specific content is separated (if applicable)
- [ ] Conditional details are in separate files when appropriate
- [ ] Clear navigation from SKILL.md to reference files

**Pattern usage:**
- [ ] Pattern 1: High-level guide with references (if applicable)
- [ ] Pattern 2: Domain-specific organization (if applicable)
- [ ] Pattern 3: Conditional details (if applicable)

## 4. Workflows and Processes

### Workflow Design
- [ ] Complex tasks broken into clear steps
- [ ] Checklists provided for complex workflows
- [ ] Each step is actionable and clear
- [ ] Decision points clearly marked
- [ ] Feedback loops implemented where needed

**Workflow checklist format:**
```markdown
Copy this checklist:

```
Task Progress:
- [ ] Step 1: Description
- [ ] Step 2: Description
- [ ] Step 3: Description
```

**Step 1: Description**
Details...

**Step 2: Description**
Details...
```

### Feedback Loops
- [ ] Validation steps for critical operations
- [ ] Clear error handling guidance
- [ ] "Run validator → fix errors → repeat" pattern where appropriate

## 5. File Paths and Technical Details

### Path Conventions
- [ ] All file paths use forward slashes (`/`)
- [ ] No Windows-style backslashes (`\`)
- [ ] Paths are clear and descriptive

### Dependencies
- [ ] Required packages are listed
- [ ] Installation instructions provided
- [ ] No assumptions about pre-installed packages

### MCP Tools (if applicable)
- [ ] MCP tool names are fully qualified: `ServerName:tool_name`
- [ ] Clear usage examples provided

## 6. Scripts (if included)

### Script Quality
- [ ] Scripts solve problems, don't punt to Claude
- [ ] Error handling is explicit and helpful
- [ ] No "magic numbers" - all constants are documented
- [ ] Clear documentation for each script
- [ ] Scripts have been tested
- [ ] Usage examples provided

**Error handling check:**
```python
# Good: Handles errors explicitly
try:
    with open(path) as f:
        return f.read()
except FileNotFoundError:
    # Create default instead of failing
    with open(path, "w") as f:
        f.write("")
    return ""

# Bad: Punts to Claude
return open(path).read()  # Will crash if file doesn't exist
```

### Script Documentation
- [ ] Clear description of what script does
- [ ] Input/output format documented
- [ ] Command-line examples provided
- [ ] Expected output shown

## 7. Templates and Examples

### Template Pattern
- [ ] Templates match strictness level to requirements
- [ ] Strict templates use "ALWAYS use this exact structure"
- [ ] Flexible templates include "use your best judgment"
- [ ] Template structure is clear and complete

### Examples Pattern
- [ ] Input/output pairs provided
- [ ] Examples cover common use cases
- [ ] Examples show desired style and detail level
- [ ] Multiple examples for variety

## 8. Common Anti-patterns

### Things to Avoid
- [ ] No Windows-style paths
- [ ] No offering too many options without clear default
- [ ] No vague terminology
- [ ] No inconsistent terminology
- [ ] No time-sensitive information (unless marked)
- [ ] No unnecessary explanations
- [ ] No first-person or second-person in description

### Directory Structure
- [ ] No README.md (unless user-facing requirement)
- [ ] No INSTALLATION_GUIDE.md
- [ ] No QUICK_REFERENCE.md
- [ ] No CHANGELOG.md
- [ ] Only essential files for AI agent

## 9. Testing and Validation

### Evaluations
- [ ] At least three evaluations created
- [ ] Evaluations test real use cases
- [ ] Baseline performance measured
- [ ] Skill improves performance vs baseline

### Model Testing
- [ ] Tested with Claude Haiku (if target model)
- [ ] Tested with Claude Sonnet (if target model)
- [ ] Tested with Claude Opus (if target model)
- [ ] Adjustments made for different model capabilities

### Real-world Usage
- [ ] Tested with real usage scenarios
- [ ] Observed how Claude navigates the skill
- [ ] Identified and fixed navigation issues
- [ ] Team feedback incorporated (if applicable)

## 10. Overall Quality Checks

### Completeness
- [ ] All required files present
- [ ] No broken references
- [ ] All scripts are executable
- [ ] All examples are valid

### Consistency
- [ ] Terminology is consistent throughout
- [ ] Formatting is consistent
- [ ] Style is consistent
- [ ] Pattern usage is consistent

### Effectiveness
- [ ] Skill solves the intended problem
- [ ] Instructions are discoverable
- [ ] Claude can successfully use the skill
- [ ] Performance improvement is measurable

## Review Summary Template

Use this template to summarize your review:

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

### 📋 Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
3. Specific actionable recommendation

### 📊 Compliance Score
- YAML Frontmatter: ✓/✗
- Content Quality: ✓/✗
- Progressive Disclosure: ✓/✗
- Workflows: ✓/✗
- Technical Details: ✓/✗
- Overall: [Pass/Needs Work/Fail]
```

## Quick Reference: Common Issues and Fixes

### Issue: Description too vague
**Fix:** Add specific triggers and use cases
```yaml
# Before
description: Helps with documents

# After
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

### Issue: SKILL.md too long
**Fix:** Split into reference files
```markdown
# In SKILL.md
## Advanced features
**Form filling**: See [forms.md](forms.md)
**API reference**: See [reference.md](reference.md)
```

### Issue: Too verbose
**Fix:** Remove unnecessary explanations
```markdown
# Before (150 tokens)
PDF (Portable Document Format) files are a common file format...
First, you'll need to install it using pip. Then you can use...

# After (50 tokens)
Use pdfplumber for text extraction:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
```

### Issue: Windows paths
**Fix:** Use forward slashes
```markdown
# Before
scripts\helper.py

# After
scripts/helper.py
```

### Issue: First person in description
**Fix:** Use third person
```yaml
# Before
description: I can help you process Excel files

# After
description: Processes Excel files and generates reports
```
