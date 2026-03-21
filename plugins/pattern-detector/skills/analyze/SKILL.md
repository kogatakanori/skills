---
name: analyze
description: Analyze conversation history to detect repetitive task patterns and suggest automation opportunities
disable-model-invocation: true
allowed-tools: Bash(python *)
---

# Pattern Analysis

Analyze your recent Claude Code conversation history to identify repetitive tasks that could be automated with skills or hooks.

## Task

Run the pattern detection script to analyze your conversation history:

```bash
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py analyze
```

The script will:
1. Read your conversation history from `~/.claude/history.jsonl`
2. Detect patterns in:
   - Repeated Bash commands (3+ occurrences)
   - File editing patterns
   - Common workflows
3. Display detected patterns with:
   - Pattern description
   - Frequency count
   - Estimated time savings
   - Suggested automation approach (skill vs hook)

## Output

The analysis will show:
- **Command Patterns**: Bash commands executed multiple times
- **File Patterns**: Files edited repeatedly
- **Workflow Patterns**: Multi-step sequences

For each pattern, you'll see:
- How many times it occurred
- When it was last executed
- Recommended automation strategy

## Next Steps

After reviewing the analysis:
1. Use `/pattern:suggest` to see detailed suggestions for creating skills/hooks
2. Use `/pattern:configure` to adjust detection sensitivity and exclusions
