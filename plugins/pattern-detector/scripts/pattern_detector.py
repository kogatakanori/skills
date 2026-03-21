#!/usr/bin/env python3
"""Main pattern detection engine and CLI interface."""

import argparse
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from history_reader import HistoryReader, format_timestamp
from storage import PatternStorage
from skill_generator import SkillGenerator


class PatternDetector:
    """Detects repetitive patterns in Claude Code conversation history."""

    def __init__(self, project_dir: Path = None):
        """
        Initialize pattern detector.

        Args:
            project_dir: Project directory (defaults to current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.history_reader = HistoryReader()
        self.storage = PatternStorage(self.project_dir)
        self.skill_generator = SkillGenerator()

    def detect_command_patterns(
        self,
        min_frequency: int = 3,
        window_size: int = 100
    ) -> List[Dict]:
        """
        Detect repeated command patterns.

        Args:
            min_frequency: Minimum occurrences to consider a pattern
            window_size: Number of recent entries to analyze

        Returns:
            List of detected command patterns
        """
        # Get recent history
        recent_entries = self.history_reader.read_recent(window_size)

        # Extract bash commands
        commands = self.history_reader.extract_bash_commands(recent_entries)

        # Count command frequencies
        command_counts = Counter(cmd['command'] for cmd in commands)

        # Load exclusions
        config = self.storage.load_config()
        exclusions = {
            exc['pattern']
            for exc in config.get('excluded_patterns', [])
            if exc['type'] == 'command'
        }

        # Find patterns meeting threshold
        patterns = []
        for command, count in command_counts.items():
            if count < min_frequency:
                continue

            # Skip excluded commands
            if command in exclusions or any(command.startswith(exc) for exc in exclusions):
                continue

            # Find occurrences
            occurrences = [
                cmd for cmd in commands
                if cmd['command'] == command
            ]

            # Calculate time savings (rough estimate: 5 seconds per command)
            estimated_time_saved = count * 5

            patterns.append({
                'type': 'command',
                'pattern': command,
                'frequency': count,
                'first_seen': min(occ['timestamp'] for occ in occurrences),
                'last_seen': max(occ['timestamp'] for occ in occurrences),
                'occurrences': occurrences,
                'estimated_time_saved': estimated_time_saved,
                'confidence': min(count / 10, 1.0)  # Higher frequency = higher confidence
            })

        # Sort by frequency (descending)
        patterns.sort(key=lambda p: p['frequency'], reverse=True)

        return patterns

    def detect_sequence_patterns(
        self,
        min_length: int = 2,
        min_frequency: int = 2,
        window_size: int = 100
    ) -> List[Dict]:
        """
        Detect repeated command sequences (workflows).

        Args:
            min_length: Minimum sequence length
            min_frequency: Minimum occurrences
            window_size: Number of recent entries to analyze

        Returns:
            List of detected sequence patterns
        """
        # Get recent history
        recent_entries = self.history_reader.read_recent(window_size)
        commands = self.history_reader.extract_bash_commands(recent_entries)

        if len(commands) < min_length:
            return []

        # Extract command sequences
        sequences = []
        for i in range(len(commands) - min_length + 1):
            seq = tuple(cmd['command'] for cmd in commands[i:i + min_length])
            sequences.append((seq, i))

        # Count sequence frequencies
        sequence_counts = Counter(seq for seq, _ in sequences)

        # Find patterns meeting threshold
        patterns = []
        for sequence, count in sequence_counts.items():
            if count < min_frequency:
                continue

            # Calculate time savings (rough estimate: 10 seconds per sequence execution)
            estimated_time_saved = count * 10

            patterns.append({
                'type': 'sequence',
                'pattern': list(sequence),
                'frequency': count,
                'estimated_time_saved': estimated_time_saved,
                'confidence': min(count / 5, 1.0)
            })

        # Sort by frequency (descending)
        patterns.sort(key=lambda p: p['frequency'], reverse=True)

        return patterns

    def analyze(self) -> Dict:
        """
        Run full pattern analysis.

        Returns:
            Dict with analysis results
        """
        config = self.storage.load_config()
        min_frequency = config.get('min_frequency', 3)

        print("🔍 Analyzing conversation history...\n")

        # Detect command patterns
        command_patterns = self.detect_command_patterns(min_frequency=min_frequency)

        # Detect sequence patterns
        sequence_patterns = self.detect_sequence_patterns(min_frequency=min_frequency)

        # Display results
        print(f"=== Command Patterns ===")
        print(f"Found {len(command_patterns)} repeated commands\n")

        for i, pattern in enumerate(command_patterns[:10], 1):
            first = format_timestamp(pattern['first_seen'])
            last = format_timestamp(pattern['last_seen'])
            print(f"{i}. Command: {pattern['pattern']}")
            print(f"   Frequency: {pattern['frequency']} times")
            print(f"   First seen: {first}")
            print(f"   Last seen: {last}")
            print(f"   Time saved if automated: ~{pattern['estimated_time_saved']}s")
            print(f"   Confidence: {pattern['confidence']:.0%}")
            print()

        if sequence_patterns:
            print(f"\n=== Workflow Sequences ===")
            print(f"Found {len(sequence_patterns)} repeated sequences\n")

            for i, pattern in enumerate(sequence_patterns[:5], 1):
                print(f"{i}. Sequence:")
                for j, cmd in enumerate(pattern['pattern'], 1):
                    print(f"   {j}. {cmd}")
                print(f"   Frequency: {pattern['frequency']} times")
                print(f"   Time saved if automated: ~{pattern['estimated_time_saved']}s")
                print()

        # Store detected patterns
        all_patterns = command_patterns + sequence_patterns
        for pattern in all_patterns:
            self.storage.save_pattern(pattern)

        return {
            'command_patterns': command_patterns,
            'sequence_patterns': sequence_patterns,
            'total_patterns': len(all_patterns)
        }

    def suggest(self, pattern_type: str = None, min_savings: int = 0):
        """
        Show automation suggestions for detected patterns.

        Args:
            pattern_type: Filter by type (skill or hook)
            min_savings: Minimum time savings in seconds
        """
        patterns = self.storage.load_patterns()

        if pattern_type:
            patterns = [p for p in patterns if p.get('suggested_type') == pattern_type]

        if min_savings > 0:
            patterns = [
                p for p in patterns
                if p.get('estimated_time_saved', 0) >= min_savings
            ]

        if not patterns:
            print("No automation suggestions found.")
            print("Run /pattern:analyze first to detect patterns.")
            return

        print(f"=== Automation Suggestions ({len(patterns)}) ===\n")

        for i, pattern in enumerate(patterns, 1):
            print(f"Pattern #{i}: {pattern.get('description', 'Unnamed pattern')}")
            print(f"├─ Type: {pattern['type']}")
            print(f"├─ Frequency: {pattern['frequency']} times")

            last_seen = pattern.get('last_seen')
            if last_seen:
                print(f"├─ Last seen: {format_timestamp(last_seen)}")

            print(f"├─ Time saved: ~{pattern.get('estimated_time_saved', 0)}s per use")

            # Generate suggestion
            suggestion = self.skill_generator.suggest_automation(pattern)
            print(f"├─ Suggestion: {suggestion['type']}")
            print(f"└─ Preview:")
            print(f"   {suggestion['preview'][:200]}...")
            print()

        print("Actions available:")
        print("  python scripts/pattern_detector.py accept <pattern-id>")
        print("  python scripts/pattern_detector.py reject <pattern-id>")

    def config_show(self):
        """Show current configuration."""
        config = self.storage.load_config()

        print("=== Pattern Detector Configuration ===\n")
        print(f"Enabled: {config.get('enabled', True)}")
        print(f"Detection Sensitivity: {config.get('detection_sensitivity', 'medium')}")
        print(f"Minimum Frequency: {config.get('min_frequency', 3)}")
        print(f"Auto Suggest: {config.get('auto_suggest', False)}")
        print(f"Suggestion Threshold: {config.get('suggestion_threshold', 5)}")

        exclusions = config.get('excluded_patterns', [])
        print(f"\nExcluded Patterns: {len(exclusions)}")
        if exclusions:
            for exc in exclusions:
                print(f"  - [{exc['type']}] {exc['pattern']}")

        print(f"\nConfiguration file: {self.storage.config_file}")

    def config_set(self, key: str, value: str):
        """Set configuration value."""
        # Parse value
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)

        config = self.storage.update_config(key, value)
        print(f"✓ Updated {key} = {value}")

    def config_exclude(self, exc_type: str, pattern: str):
        """Add exclusion pattern."""
        self.storage.add_exclusion(exc_type, pattern)
        print(f"✓ Added exclusion: [{exc_type}] {pattern}")

    def config_unexclude(self, exc_type: str, pattern: str):
        """Remove exclusion pattern."""
        if self.storage.remove_exclusion(exc_type, pattern):
            print(f"✓ Removed exclusion: [{exc_type}] {pattern}")
        else:
            print(f"✗ Exclusion not found: [{exc_type}] {pattern}")

    def config_reset(self):
        """Reset configuration to defaults."""
        self.storage.reset_config()
        print("✓ Configuration reset to defaults")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Pattern detection for Claude Code')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Analyze command
    parser_analyze = subparsers.add_parser('analyze', help='Analyze conversation history')
    parser_analyze.set_defaults(func=lambda args: PatternDetector().analyze())

    # Suggest command
    parser_suggest = subparsers.add_parser('suggest', help='Show automation suggestions')
    parser_suggest.add_argument('--type', choices=['skill', 'hook'], help='Filter by type')
    parser_suggest.add_argument('--min-savings', type=int, default=0, help='Minimum time savings')
    parser_suggest.set_defaults(
        func=lambda args: PatternDetector().suggest(args.type, args.min_savings)
    )

    # Config command
    parser_config = subparsers.add_parser('config', help='Manage configuration')
    config_subparsers = parser_config.add_subparsers(dest='config_action', help='Config action')

    # Config show
    parser_config_show = config_subparsers.add_parser('show', help='Show current configuration')
    parser_config_show.set_defaults(func=lambda args: PatternDetector().config_show())

    # Config set
    parser_config_set = config_subparsers.add_parser('set', help='Set configuration value')
    parser_config_set.add_argument('key', help='Configuration key')
    parser_config_set.add_argument('value', help='Configuration value')
    parser_config_set.set_defaults(func=lambda args: PatternDetector().config_set(args.key, args.value))

    # Config exclude
    parser_config_exclude = config_subparsers.add_parser('exclude', help='Add exclusion pattern')
    parser_config_exclude.add_argument('type', choices=['command', 'file', 'conversation'], help='Exclusion type')
    parser_config_exclude.add_argument('pattern', help='Pattern to exclude')
    parser_config_exclude.set_defaults(func=lambda args: PatternDetector().config_exclude(args.type, args.pattern))

    # Config unexclude
    parser_config_unexclude = config_subparsers.add_parser('unexclude', help='Remove exclusion pattern')
    parser_config_unexclude.add_argument('type', choices=['command', 'file', 'conversation'], help='Exclusion type')
    parser_config_unexclude.add_argument('pattern', help='Pattern to remove')
    parser_config_unexclude.set_defaults(func=lambda args: PatternDetector().config_unexclude(args.type, args.pattern))

    # Config reset
    parser_config_reset = config_subparsers.add_parser('reset', help='Reset configuration to defaults')
    parser_config_reset.set_defaults(func=lambda args: PatternDetector().config_reset())

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # Default: run analyze
        PatternDetector().analyze()


if __name__ == '__main__':
    main()
