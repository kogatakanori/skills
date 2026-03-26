---
name: verifying-consistency
description: Verifies consistency of changed files against the main branch. Checks documents for contradictions, duplications, gaps, terminology inconsistencies, and logical leaps. Also checks alignment between documentation and implementation code. Use when the user asks to check, verify, or review consistency of documents or code changes.
user_invocable: true
---

# Verifying Consistency

Verify consistency of all files changed from the main branch, including uncommitted changes.

## Workflow

### Step 1: Collect changed files

Run `git diff main --name-only` to get all changed files (committed and uncommitted).

### Step 2: Classify files

Classify each changed file into:
- **Documents**: `.md`, `.txt`, `.csv`, `.json`, `.yaml`, `.yml`, `.toml`, `.rst`, `.adoc` and similar
- **Code**: `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.rb`, `.sh` and similar
- **Mixed**: Files that contain both documentation and code (e.g., inline docs)

### Step 3: Launch subagents in parallel

Based on the classification, launch the appropriate Agent subagents in parallel:

#### Agent A: Document Consistency Check

Launch when documents exist in the changed files.

Prompt for Agent A:
```
You are a document consistency checker. Read ALL of the following changed document files and perform a thorough consistency check.

Changed document files: [list files here]

Check for the following issues across ALL files:
1. Contradictions - conflicting statements between or within files
2. Duplications - same content repeated unnecessarily
3. Gaps/Omissions - missing information that should be present based on context
4. Terminology inconsistencies - same concept referred to by different terms
5. Logical leaps - conclusions or statements without supporting context

Read each file completely before checking. Cross-reference between files to find inter-file inconsistencies.

Output format:

## Summary Table

| # | File | Location | Type | Issue |
|---|------|----------|------|-------|
| 1 | file.md | L12-15 | Contradiction | Brief description |

## Details

### Issue 1: [Brief title]
- **File**: file.md (L12-15)
- **Type**: Contradiction
- **Problem**: Detailed description of the issue
- **Suggested fix**: Specific recommendation for resolution

(Repeat for each issue found)

If no issues are found, report that clearly.
```

#### Agent B: Document-Code Alignment Check

Launch when BOTH documents and code exist in the changed files.

Prompt for Agent B:
```
You are a document-code alignment checker. Read ALL of the following changed files and verify that documentation accurately reflects the implementation.

Changed document files: [list document files here]
Changed code files: [list code files here]

Check for:
1. Specifications described in docs but not implemented in code
2. Implementations in code not documented
3. Discrepancies between documented behavior and actual code logic
4. Outdated documentation that doesn't match current code
5. Parameter/argument mismatches between docs and code

Read each file completely before checking.

Output format:

## Summary Table

| # | Doc File | Code File | Type | Issue |
|---|----------|-----------|------|-------|
| 1 | spec.md | app.py | Not implemented | Brief description |

## Details

### Issue 1: [Brief title]
- **Doc file**: spec.md (L12-15)
- **Code file**: app.py (L30-45)
- **Type**: Not implemented
- **Problem**: Detailed description of the discrepancy
- **Suggested fix**: Specific recommendation for resolution

(Repeat for each issue found)

If no issues are found, report that clearly.
```

### Step 4: Consolidate results

After both agents complete, consolidate the results into a single report:

```markdown
# Consistency Check Report

## Overview
- Changed files: N files
- Documents checked: N files
- Code files checked: N files
- Issues found: N issues

## Document Consistency (Agent A)
[Agent A results - summary table then details]

## Document-Code Alignment (Agent B)
[Agent B results - summary table then details]
```

## Notes

- If only documents changed (no code), skip Agent B
- If only code changed (no documents), skip Agent A
- If both exist, run Agent A and Agent B in parallel
- Every invocation performs a full check from scratch
