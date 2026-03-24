# Pattern Detector Plugin

Automatically detect repetitive tasks in your Claude Code workflow and suggest creating skills or hooks to automate them.

## Overview

Pattern Detector analyzes your conversation history to identify repeated commands, user prompts, file operations, and workflows. Using semantic similarity detection, it can find patterns even when your instructions are worded differently. When it finds patterns, it suggests automation opportunities and can even generate skills or hooks for you automatically.

## Features

- Analyze conversation history for repetitive patterns
- Detect repeated Bash commands (3+ occurrences by default)
- Detect repeated user prompts using semantic similarity (NEW!)
- Identify multi-step workflow sequences
- Suggest skills or hooks for automation
- Auto-generate SKILL.md files
- Configurable detection sensitivity and exclusions
- Project-specific pattern storage

## Installation

### Using `--plugin-dir` (Development/Testing)

```bash
claude --plugin-dir /path/to/pattern-detector
```

### Add to Marketplace

1. Add this plugin to your marketplace JSON:

```json
{
  "plugins": [
    {
      "name": "pattern-detector",
      "description": "Detect repetitive tasks and suggest automation",
      "source": "./pattern-detector",
      "strict": false,
      "skills": ["./pattern-detector/skills"]
    }
  ]
}
```

2. Reload plugins:

```bash
/reload-plugins
```

## Quick Start

### 1. Analyze Your Workflow

Run pattern detection on your conversation history:

```bash
/pattern-detector-analyze
```

This will:

- Read your `~/.claude/history.jsonl`
- Detect repeated commands and workflows
- Display patterns with frequency and time savings estimates
- Store detected patterns in `.pattern-detector/`

### 2. Review Suggestions

See detailed automation suggestions:

```bash
/pattern-detector-suggest
```

For each pattern, you'll see:

- Pattern description and frequency
- Estimated time savings
- Suggested automation approach (skill vs hook)
- Preview of generated SKILL.md or hook config

### 3. Accept or Reject Patterns

For patterns suggested as skills, you can:

**Accept** - Generate the skill automatically:

```bash
python scripts/pattern_detector.py accept 1
```

**Reject** - Exclude from future suggestions:

```bash
python scripts/pattern_detector.py reject 2
```

### 4. Configure Detection

Adjust sensitivity and exclusions:

```bash
/pattern-detector-configure
```

## Commands

### `/pattern-detector-analyze`

Analyze conversation history to detect repetitive patterns.

**Example:**

```bash
/pattern-detector-analyze
```

**Output:**

```
=== Command Patterns ===
Found 3 repeated commands

1. Command: npm test
   Frequency: 5 times
   Last seen: 2024-03-20 14:32:10
   Time saved if automated: ~25s
   Confidence: 50%

2. Command: git add . && git commit -m "..."
   Frequency: 4 times
   ...

=== Prompt Patterns ===
Found 2 repeated prompts

1. Pattern: テストを実行して
   Frequency: 7 times
   First seen: 2024-03-15 10:15:30
   Last seen: 2024-03-20 16:45:22
   Time saved if automated: ~210s
   Confidence: 85%
   Examples:
     - テストを実行してください
     - テストを実行して

2. Pattern: コミットしてください
   Frequency: 5 times
   ...
```

### `/pattern-detector-suggest`

Show automation suggestions for detected patterns.

**Options:**

- `--type skill`: Show only skill suggestions
- `--type hook`: Show only hook suggestions
- `--min-savings <seconds>`: Filter by minimum time savings

**Example:**

```bash
/pattern-detector-suggest --min-savings 30
```

### Accept/Reject Patterns

After reviewing suggestions, you can accept or reject patterns:

#### Accept a Pattern

Generate a skill automatically in `.claude/skills/`:

```bash
python scripts/pattern_detector.py accept <pattern-id>
```

**Example:**

```bash
python scripts/pattern_detector.py accept 1
```

This will:
- Create a new skill in `.claude/skills/{skill-name}/SKILL.md`
- Mark the pattern as "accepted"
- Make the skill available for immediate use

#### Reject a Pattern

Mark a pattern as not worth automating and exclude it from future detections:

```bash
python scripts/pattern_detector.py reject <pattern-id>
```

**Example:**

```bash
python scripts/pattern_detector.py reject 2
```

This will:
- Add the pattern to your exclusion list
- Mark the pattern as "rejected"
- Prevent it from appearing in future suggestions

### `/pattern-detector-configure`

Configure pattern detection settings.

**Available settings:**

- `sensitivity`: low, medium (default), high
- `min-frequency`: Minimum occurrences (default: 3)
- `auto-suggest`: Enable automatic suggestions (default: false)
- `suggestion-threshold`: Occurrences before auto-suggesting (default: 5)

**Example:**

```bash
python scripts/pattern_detector.py config set sensitivity high
python scripts/pattern_detector.py config set min-frequency 5
```

**Exclusions:**

```bash
# Exclude a command from detection
python scripts/pattern_detector.py config exclude command "ls"

# Exclude a prompt pattern from detection
python scripts/pattern_detector.py config exclude prompt "テストを実行"

# Remove an exclusion
python scripts/pattern_detector.py config unexclude command "ls"
python scripts/pattern_detector.py config unexclude prompt "テストを実行"
```

## How It Works

### Pattern Detection

Pattern Detector analyzes your conversation history using multiple strategies:

1. **Exact Command Matching**: Counts identical Bash commands
2. **Prompt Similarity Detection**: Identifies semantically similar user prompts using:
   - Text normalization (lowercase, whitespace)
   - Keyword extraction and Jaccard similarity
   - Sequence matching for contextual similarity
   - Configurable similarity threshold (default: 70%)
3. **Sequence Detection**: Identifies repeated multi-step workflows
4. **Frequency Threshold**: Only suggests patterns meeting minimum occurrences

### Automation Suggestion

For each detected pattern, the plugin determines:

- **Skill**: For commands with side effects (commit, deploy, etc.) that should be user-triggered
- **Hook**: For automated tasks (linting, formatting) that can run after file changes

### Skill Generation

When you accept a suggestion, Pattern Detector generates:

- Complete SKILL.md file with YAML frontmatter
- Descriptive instructions
- Estimated time savings in description

## Configuration

### Default Configuration

```json
{
  "enabled": true,
  "detection_sensitivity": "medium",
  "min_frequency": 3,
  "auto_suggest": false,
  "suggestion_threshold": 5,
  "excluded_patterns": []
}
```

### Detection Sensitivity

- **Low**: Detects only frequently repeated patterns (5+ occurrences)
- **Medium** (default): Balanced detection (3+ occurrences)
- **High**: Aggressive detection (2+ occurrences, may produce false positives)

### Excluded Patterns

Common commands are excluded by default:

- Basic: `ls`, `cd`, `pwd`
- Git read-only: `git status`, `git log`, `git diff`
- Help: `--help`, `-h`, `man`
- File reading: `cat`, `head`, `tail`, `less`

See [config/default_exclusions.json](config/default_exclusions.json) for the full list.

## Project Structure

```
pattern-detector/
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata
├── skills/
│   ├── pattern-detector-analyze/
│   │   └── SKILL.md            # /pattern-detector-analyze command
│   ├── pattern-detector-suggest/
│   │   └── SKILL.md            # /pattern-detector-suggest command
│   └── pattern-detector-configure/
│       └── SKILL.md            # /pattern-detector-configure command
├── scripts/
│   ├── history_reader.py       # Parse history.jsonl
│   ├── pattern_detector.py     # Main detection engine
│   ├── prompt_similarity.py    # Prompt similarity detection
│   ├── storage.py              # Pattern storage management
│   └── skill_generator.py      # Generate SKILL.md files
├── config/
│   └── default_exclusions.json # Default excluded patterns
└── README.md
```

### Data Storage

Pattern Detector stores data in your project directory:

```
your-project/
└── .pattern-detector/
    ├── detected_patterns.jsonl  # All detected patterns
    ├── config.json               # Project-specific configuration
    └── exclusions.json           # Custom exclusions
```

**Recommendation**: Add `.pattern-detector/` to your `.gitignore`:

```gitignore
# Pattern Detector runtime data
.pattern-detector/detected_patterns.jsonl
.pattern-detector/config.json
```

## Examples

### Example 1: Repeated Test Command

**Detected Pattern:**

```
Command: npm test
Frequency: 7 times
Time saved: ~35 seconds
```

**Generated Skill:**

````yaml
---
name: test
description: Run test suite (detected 7 times)
---

# Run Tests

Execute the test suite:

```bash
npm test
````

````

**Usage:**
```bash
/test
````

### Example 2: Test & Commit Workflow

**Detected Pattern:**

```
Sequence:
1. npm test
2. git add .
3. git commit -m "..."
Frequency: 5 times
Time saved: ~50 seconds
```

**Generated Skill:**

```yaml
---
name: test-and-commit
description: Run tests and commit if they pass

---
# Test and Commit Workflow

1. Run npm test
2. If tests pass, stage changes with git add .
3. Prompt for commit message
4. Create commit
```

**Usage:**

```bash
/test-and-commit
```

### Example 3: Repeated Prompt Pattern

**Detected Pattern:**

```
Pattern: テストを実行してください
Frequency: 8 times
Similarity: 85%
Examples:
  - テストを実行してください
  - テストを実行して
  - Run the tests please
Time saved: ~240 seconds
```

**Generated Skill:**

```yaml
---
name: run-tests
description: テストを実行してください
user_invocable: true
---

# Run Tests

このスキルは、繰り返し実行されたプロンプトパターンから自動生成されました。

## 元のプロンプト

テストを実行してください

## 検出情報

- 頻度: 8回
- 推定時間節約: ~240秒

## 実行内容

テストを実行してください
```

**Usage:**

```bash
/run-tests
```

## Troubleshooting

### No patterns detected

1. Ensure you have sufficient conversation history (`~/.claude/history.jsonl`)
2. Lower the `min-frequency` threshold
3. Check if commands are in the exclusion list

### Too many false positives

1. Increase the `min-frequency` threshold
2. Set sensitivity to `low`
3. Add patterns to the exclusion list

### Plugin not loading

1. Verify plugin structure is correct
2. Check `plugin.json` is valid JSON
3. Run `/reload-plugins`
4. Check for Python errors in terminal

## Development

### Running Tests

```bash
# Test history reader
python scripts/history_reader.py

# Test pattern detector
python scripts/pattern_detector.py

# Test storage
python scripts/storage.py

# Test skill generator
python scripts/skill_generator.py
```

### Future Enhancements (Roadmap)

**Phase 2 Features:**

- [x] ✅ Semantic prompt similarity detection
- [ ] Automatic pattern detection with hooks
- [ ] Real-time suggestions during workflow
- [ ] File operation pattern detection
- [ ] Custom automation templates

**Phase 3 Features:**

- [x] ✅ Sequence detection (multi-step workflows)
- [ ] Agent-based interactive customization
- [ ] Statistical analysis dashboard
- [ ] Cross-project pattern analysis
- [ ] Improved multilingual prompt detection (Japanese + English)

**Phase 4 Features:**

- [ ] Integration with hookify plugin
- [ ] ML-based pattern prediction with embeddings
- [ ] Team pattern sharing
- [ ] Context-aware skill suggestions

## Privacy

- **100% Local**: All analysis runs locally, no data is sent externally
- **Read-Only History**: Only reads `~/.claude/history.jsonl`, never modifies it
- **Project-Scoped**: Patterns are stored per-project in `.pattern-detector/`
- **Configurable Exclusions**: Exclude sensitive patterns or projects

## License

MIT

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues or questions:

- Open an issue on GitHub
- Check existing issues for solutions
- Review the [troubleshooting](#troubleshooting) section

## Credits

Created by Takanori Koga

Inspired by the need to reduce repetitive tasks in software development workflows.
