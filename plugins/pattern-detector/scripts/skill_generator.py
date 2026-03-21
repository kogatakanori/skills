#!/usr/bin/env python3
"""Generate skill and hook definitions from detected patterns."""

from pathlib import Path
from typing import Dict


class SkillGenerator:
    """Generates skills and hooks from detected patterns."""

    def suggest_automation(self, pattern: Dict) -> Dict:
        """
        Suggest automation approach for a pattern.

        Args:
            pattern: Detected pattern dictionary

        Returns:
            Dict with suggestion type and preview
        """
        pattern_type = pattern.get('type')

        if pattern_type == 'command':
            return self._suggest_command_automation(pattern)
        elif pattern_type == 'sequence':
            return self._suggest_sequence_automation(pattern)
        elif pattern_type == 'prompt':
            return self._suggest_prompt_automation(pattern)
        else:
            return {
                'type': 'skill',
                'preview': 'No specific automation suggested'
            }

    def _suggest_command_automation(self, pattern: Dict) -> Dict:
        """Suggest automation for a repeated command."""
        command = pattern.get('pattern', '')
        frequency = pattern.get('frequency', 0)

        # Determine if this should be a skill or hook
        # Commands with side effects (git commit, deploy, etc.) → skill
        # Read-only commands or formatting → could be hook

        is_destructive = any(
            keyword in command.lower()
            for keyword in ['commit', 'push', 'deploy', 'delete', 'rm', 'drop']
        )

        if is_destructive:
            # Suggest as skill (user-triggered)
            suggestion_type = 'skill'
            skill_name = self._generate_skill_name(command)

            preview = f"""---
name: {skill_name}
description: {command} (detected {frequency} times)
---

# {skill_name.replace('-', ' ').title()}

Execute the following command:

```bash
{command}
```

Confirm before executing.
"""
        else:
            # Suggest as hook (automatic)
            suggestion_type = 'hook'

            preview = f"""Hook suggestion for: {command}

This command could be automated with a PostToolUse hook.

Example hook configuration:
```json
{{
  "hooks": {{
    "PostToolUse": [
      {{
        "matcher": "Edit|Write",
        "hooks": [
          {{
            "type": "command",
            "command": "{command}"
          }}
        ]
      }}
    ]
  }}
}}
```

This will run '{command}' automatically after file edits.
"""

        return {
            'type': suggestion_type,
            'preview': preview,
            'skill_name': skill_name if suggestion_type == 'skill' else None
        }

    def _suggest_sequence_automation(self, pattern: Dict) -> Dict:
        """Suggest automation for a repeated command sequence."""
        sequence = pattern.get('pattern', [])
        frequency = pattern.get('frequency', 0)

        # Sequences are typically workflows → suggest as skill
        skill_name = 'workflow-' + '-'.join(
            cmd.split()[0] for cmd in sequence[:3]
        ).lower()[:30]

        steps = '\n'.join(f"{i}. {cmd}" for i, cmd in enumerate(sequence, 1))

        preview = f"""---
name: {skill_name}
description: Workflow sequence (detected {frequency} times)
---

# Automated Workflow

Execute the following workflow:

{steps}

Run each step in sequence, stopping if any step fails.
"""

        return {
            'type': 'skill',
            'preview': preview,
            'skill_name': skill_name
        }

    def _suggest_prompt_automation(self, pattern: Dict) -> Dict:
        """Suggest automation for a repeated prompt pattern."""
        prompt_text = pattern.get('pattern', '')
        frequency = pattern.get('frequency', 0)
        examples = pattern.get('examples', [])

        # Generate skill name from prompt
        skill_name = self._generate_skill_name_from_prompt(prompt_text)

        # Create a concise description
        description = prompt_text[:100] + ('...' if len(prompt_text) > 100 else '')

        preview = f"""---
name: {skill_name}
description: {description}
user_invocable: true
---

# {skill_name.replace('-', ' ').title()}

このスキルは、繰り返し実行されたプロンプトパターンから自動生成されました。

## 元のプロンプト

{prompt_text}

## 検出情報

- 頻度: {frequency}回
- 推定時間節約: ~{pattern.get('estimated_time_saved', 0)}秒

## 使用例

以下のような指示がこのパターンに含まれます:

"""

        # Add examples
        for i, example in enumerate(examples[:3], 1):
            preview += f"{i}. {example}\n"

        preview += """
## 実行内容

以下の処理を実行します:

"""
        preview += prompt_text

        return {
            'type': 'skill',
            'preview': preview,
            'skill_name': skill_name
        }

    def _generate_skill_name_from_prompt(self, prompt: str) -> str:
        """
        Generate a skill name from a prompt.

        Args:
            prompt: Prompt text

        Returns:
            Skill name (kebab-case)
        """
        import re

        # Extract key words from prompt (first few meaningful words)
        words = re.findall(r'\b\w+\b', prompt.lower())

        # Filter out common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'please', 'can', 'you', 'could', 'would', 'should', 'make', 'do',
            'してください', 'して', 'を', 'の', 'に', 'が', 'は', 'で'
        }

        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]

        # Take first 3 meaningful words
        skill_parts = meaningful_words[:3]

        if not skill_parts:
            skill_parts = ['auto', 'task']

        # Convert to kebab-case
        skill_name = '-'.join(skill_parts)

        # Sanitize
        skill_name = re.sub(r'[^a-z0-9-]', '-', skill_name)
        skill_name = re.sub(r'-+', '-', skill_name)
        skill_name = skill_name.strip('-')

        # Limit length
        if len(skill_name) > 64:
            skill_name = skill_name[:64].rstrip('-')

        return skill_name or 'auto-prompt'

    def _generate_skill_name(self, command: str) -> str:
        """
        Generate a skill name from a command.

        Args:
            command: Command string

        Returns:
            Skill name (kebab-case)
        """
        # Extract the main command (first word)
        parts = command.split()
        if not parts:
            return 'auto-command'

        # Build skill name from command parts
        skill_parts = []

        # Add main command
        skill_parts.append(parts[0])

        # Add significant arguments (skip flags)
        for part in parts[1:]:
            if not part.startswith('-') and len(skill_parts) < 3:
                skill_parts.append(part.strip('"\''))

        # Convert to kebab-case
        skill_name = '-'.join(skill_parts).lower()

        # Sanitize (only lowercase, numbers, hyphens)
        skill_name = ''.join(
            c if c.isalnum() or c == '-' else '-'
            for c in skill_name
        )

        # Remove consecutive hyphens
        while '--' in skill_name:
            skill_name = skill_name.replace('--', '-')

        # Trim hyphens from start/end
        skill_name = skill_name.strip('-')

        # Limit length
        if len(skill_name) > 64:
            skill_name = skill_name[:64].rstrip('-')

        return skill_name or 'auto-command'

    def generate_skill_file(
        self,
        pattern: Dict,
        output_dir: Path
    ) -> Path:
        """
        Generate a complete SKILL.md file.

        Args:
            pattern: Detected pattern
            output_dir: Directory to write skill file

        Returns:
            Path to generated skill file
        """
        suggestion = self.suggest_automation(pattern)

        if suggestion['type'] != 'skill':
            raise ValueError("Pattern is not suitable for skill generation")

        skill_name = suggestion['skill_name']
        skill_dir = output_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_file = skill_dir / 'SKILL.md'
        skill_file.write_text(suggestion['preview'])

        return skill_file


if __name__ == '__main__':
    # Example usage
    generator = SkillGenerator()

    # Example command pattern
    pattern = {
        'type': 'command',
        'pattern': 'npm test',
        'frequency': 5
    }

    suggestion = generator.suggest_automation(pattern)
    print("=== Automation Suggestion ===")
    print(f"Type: {suggestion['type']}")
    print(f"\nPreview:\n{suggestion['preview']}")
