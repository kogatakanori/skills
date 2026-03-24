---
name: pattern-detector-suggest
description: Show detailed suggestions for automating detected patterns with skills or hooks
user-invocable: true
---

# Pattern Automation Suggestions

View and act on suggestions for automating repetitive patterns detected in your workflow.

## Task

Display all pending automation suggestions:

```bash
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py suggest
```

## What You'll See

For each suggested automation, you'll see:

### Pattern Information

- **Pattern Type**: Command, File Edit, or Workflow sequence
- **Description**: What the pattern does
- **Frequency**: How many times it's been detected
- **Last Occurrence**: When you last performed this pattern
- **Estimated Time Saved**: Projected efficiency gain

### Automation Recommendation

- **Suggested Approach**: Skill or Hook
- **Implementation Preview**: Example SKILL.md or hook configuration
- **Complexity**: Easy, Medium, or Complex

## Actions Available

For each suggestion, you can:

1. **Accept**: Generate the skill or hook automatically

   ```bash
   python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py accept <pattern-id>
   ```

2. **Customize**: Use an Agent to interactively refine the automation

   ```bash
   python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py customize <pattern-id>
   ```

3. **Reject**: Mark the pattern as not worth automating

   ```bash
   python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py reject <pattern-id>
   ```

4. **Snooze**: Remind me later (after N more occurrences)
   ```bash
   python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py snooze <pattern-id> <count>
   ```

## Example Output

```
Pattern #1: Repeated Test & Commit Workflow
├─ Type: Workflow Sequence
├─ Frequency: 7 times (last: 2 hours ago)
├─ Commands: npm test → git add . → git commit -m "..."
├─ Time Saved: ~3 minutes per use
├─ Suggestion: Create a skill /test-and-commit
└─ Preview:
   ---
   name: test-and-commit
   description: Run tests and commit changes if they pass
   ---

   Run the test suite and commit changes:
   1. Run npm test
   2. If tests pass, stage changes with git add .
   3. Prompt for commit message
   4. Create commit

Actions: [A]ccept | [C]ustomize | [R]eject | [S]nooze
```

## Filtering Suggestions

Show only specific types:

```bash
# Show only skill suggestions
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py suggest --type skill

# Show only hook suggestions
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py suggest --type hook

# Show patterns with high time savings (>60 seconds)
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py suggest --min-savings 60
```
