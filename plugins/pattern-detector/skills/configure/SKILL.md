---
name: configure
description: Configure pattern detection settings including sensitivity, exclusions, and notification preferences
disable-model-invocation: true
allowed-tools: Bash(python *), Read, Write
---

# Pattern Detection Configuration

Configure how pattern-detector analyzes your workflow and suggests automation.

## Current Configuration

View current settings:

```bash
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config show
```

## Configuration Options

### Detection Sensitivity

Control how aggressively patterns are detected:

```bash
# Set sensitivity: low, medium, or high
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config set sensitivity medium
```

- **Low**: Detects only frequently repeated patterns (5+ occurrences)
- **Medium** (default): Balanced detection (3+ occurrences)
- **High**: Aggressive detection (2+ occurrences, may produce more false positives)

### Minimum Frequency

Set the minimum number of occurrences before suggesting automation:

```bash
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config set min-frequency 3
```

### Exclusion Patterns

Exclude specific commands or patterns from detection:

```bash
# Add a command to exclusions
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config exclude command "ls"
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config exclude command "git status"

# Add a file pattern to exclusions
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config exclude file "**/.git/**"

# Add a conversation pattern to exclusions
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config exclude conversation "hello"
```

Remove exclusions:

```bash
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config unexclude command "ls"
```

### Auto-Suggestion

Enable or disable automatic suggestions:

```bash
# Enable automatic suggestions during your workflow
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config set auto-suggest true

# Disable (manual analysis only with /pattern:analyze)
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config set auto-suggest false
```

### Suggestion Threshold

Set how many occurrences trigger an automatic suggestion:

```bash
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config set suggestion-threshold 5
```

## Default Exclusions

Common commands that are typically excluded by default:
- Basic commands: `ls`, `cd`, `pwd`, `git status`
- Help commands: `--help`, `-h`, `man`
- Read-only operations: `cat`, `head`, `tail`, `less`

View all default exclusions:

```bash
cat ${CLAUDE_SKILL_DIR}/../../config/default_exclusions.json
```

## Configuration File

Your configuration is stored in your project's `.pattern-detector/config.json`.

To edit manually:

```bash
# Open configuration file
open .pattern-detector/config.json
```

Example configuration:

```json
{
  "enabled": true,
  "detection_sensitivity": "medium",
  "min_frequency": 3,
  "auto_suggest": true,
  "suggestion_threshold": 5,
  "excluded_patterns": [
    { "type": "command", "pattern": "ls" },
    { "type": "command", "pattern": "git status" },
    { "type": "file", "pattern": "**/.git/**" }
  ]
}
```

## Reset to Defaults

Reset all configuration to defaults:

```bash
python ${CLAUDE_SKILL_DIR}/../../scripts/pattern_detector.py config reset
```
