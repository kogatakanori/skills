#!/usr/bin/env python3
"""Read and parse Claude Code conversation history from history.jsonl."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from constants import BASH_INDICATORS


class HistoryReader:
    """Reads and parses Claude Code conversation history."""

    def __init__(self, history_path: Optional[Path] = None):
        """
        Initialize history reader.

        Args:
            history_path: Path to history.jsonl file (defaults to ~/.claude/history.jsonl)
        """
        if history_path is None:
            history_path = Path.home() / '.claude' / 'history.jsonl'
        self.history_path = Path(history_path)

        if not self.history_path.exists():
            raise FileNotFoundError(f"History file not found: {self.history_path}")

    def read_all(self) -> List[Dict]:
        """
        Read all entries from history file.

        Returns:
            List of history entry dictionaries
        """
        entries = []
        with open(self.history_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
        return entries

    def read_recent(self, n: int = 100) -> List[Dict]:
        """
        Read the N most recent entries.

        Args:
            n: Number of recent entries to return

        Returns:
            List of recent history entries
        """
        entries = self.read_all()
        return entries[-n:] if len(entries) > n else entries

    def read_by_project(self, project_path: str) -> List[Dict]:
        """
        Read entries for a specific project.

        Args:
            project_path: Path to the project directory

        Returns:
            List of entries for the specified project
        """
        entries = self.read_all()
        project_path = os.path.normpath(project_path)

        return [
            entry for entry in entries
            if entry.get('project') and os.path.normpath(entry['project']) == project_path
        ]

    def read_by_session(self, session_id: str) -> List[Dict]:
        """
        Read entries for a specific session.

        Args:
            session_id: Session ID to filter by

        Returns:
            List of entries for the specified session
        """
        entries = self.read_all()
        return [
            entry for entry in entries
            if entry.get('sessionId') == session_id
        ]

    def read_since(self, timestamp: int) -> List[Dict]:
        """
        Read entries since a specific timestamp.

        Args:
            timestamp: Unix timestamp in milliseconds

        Returns:
            List of entries since the timestamp
        """
        entries = self.read_all()
        return [
            entry for entry in entries
            if entry.get('timestamp', 0) >= timestamp
        ]

    def extract_bash_commands(self, entries: List[Dict]) -> List[Dict]:
        """
        Extract Bash commands from history entries.

        Args:
            entries: List of history entries

        Returns:
            List of dicts with command info (command, timestamp, project)
        """
        commands = []

        for entry in entries:
            display = entry.get('display', '')

            if any(display.startswith(cmd) for cmd in BASH_INDICATORS):
                commands.append({
                    'command': display,
                    'timestamp': entry.get('timestamp'),
                    'project': entry.get('project'),
                    'session': entry.get('sessionId')
                })

        return commands

    def extract_user_prompts(self, entries: List[Dict]) -> List[Dict]:
        """
        Extract user prompts from history entries.

        Args:
            entries: List of history entries

        Returns:
            List of dicts with prompt info (prompt, timestamp, project)
        """
        prompts = []

        for entry in entries:
            # Extract user messages from the display field
            display = entry.get('display', '')

            # Skip empty or very short prompts
            if len(display.strip()) < 10:
                continue

            # Skip if it looks like a command (starts with /)
            if display.strip().startswith('/'):
                continue

            # Skip if it's a bash command
            if any(display.startswith(cmd) for cmd in BASH_INDICATORS):
                continue

            prompts.append({
                'prompt': display,
                'timestamp': entry.get('timestamp'),
                'project': entry.get('project'),
                'session': entry.get('sessionId')
            })

        return prompts

    def extract_file_operations(self, entries: List[Dict]) -> List[Dict]:
        """
        Extract file operation patterns from history entries.

        Args:
            entries: List of history entries

        Returns:
            List of dicts with file operation info
        """
        # This is a placeholder - in a full implementation, we would parse
        # tool usage from the history to identify Read, Edit, Write operations
        # For now, we'll return an empty list
        return []

    def get_session_info(self) -> Dict[str, int]:
        """
        Get summary statistics about sessions.

        Returns:
            Dict with session statistics
        """
        entries = self.read_all()
        sessions = set()
        projects = set()

        for entry in entries:
            if entry.get('sessionId'):
                sessions.add(entry['sessionId'])
            if entry.get('project'):
                projects.add(entry['project'])

        return {
            'total_entries': len(entries),
            'total_sessions': len(sessions),
            'total_projects': len(projects),
            'oldest_timestamp': entries[0].get('timestamp') if entries else None,
            'newest_timestamp': entries[-1].get('timestamp') if entries else None
        }


def format_timestamp(timestamp_ms: int) -> str:
    """
    Format a timestamp in milliseconds to a human-readable string.

    Args:
        timestamp_ms: Unix timestamp in milliseconds

    Returns:
        Formatted timestamp string
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    # Example usage
    reader = HistoryReader()

    print("=== History Statistics ===")
    stats = reader.get_session_info()
    for key, value in stats.items():
        if 'timestamp' in key and value:
            print(f"{key}: {format_timestamp(value)}")
        else:
            print(f"{key}: {value}")

    print("\n=== Recent Bash Commands ===")
    recent = reader.read_recent(50)
    commands = reader.extract_bash_commands(recent)
    for cmd in commands[-10:]:
        ts = format_timestamp(cmd['timestamp'])
        print(f"[{ts}] {cmd['command']}")
