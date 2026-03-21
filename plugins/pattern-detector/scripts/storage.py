#!/usr/bin/env python3
"""Storage management for detected patterns and configuration."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class PatternStorage:
    """Manages storage of detected patterns and configuration."""

    def __init__(self, project_dir: Path = None):
        """
        Initialize pattern storage.

        Args:
            project_dir: Project directory (defaults to current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.storage_dir = self.project_dir / '.pattern-detector'
        self.patterns_file = self.storage_dir / 'detected_patterns.jsonl'
        self.config_file = self.storage_dir / 'config.json'
        self.exclusions_file = self.storage_dir / 'exclusions.json'

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(exist_ok=True)

        # Initialize config if it doesn't exist
        if not self.config_file.exists():
            self._init_default_config()

    def _init_default_config(self):
        """Initialize default configuration."""
        default_config = {
            "enabled": True,
            "detection_sensitivity": "medium",
            "min_frequency": 3,
            "auto_suggest": False,
            "suggestion_threshold": 5,
            "excluded_patterns": []
        }
        self.save_config(default_config)

    def save_pattern(self, pattern: Dict) -> str:
        """
        Save a detected pattern.

        Args:
            pattern: Pattern dictionary

        Returns:
            Pattern ID
        """
        # Generate pattern ID if not present
        if 'id' not in pattern:
            pattern['id'] = str(uuid.uuid4())[:8]

        # Add metadata
        pattern['detected_at'] = pattern.get('detected_at', datetime.now().isoformat())
        pattern['status'] = pattern.get('status', 'pending')

        # Append to patterns file (JSONL format)
        with open(self.patterns_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(pattern) + '\n')

        return pattern['id']

    def load_patterns(self, status: Optional[str] = None) -> List[Dict]:
        """
        Load detected patterns.

        Args:
            status: Filter by status (pending, suggested, accepted, rejected)

        Returns:
            List of patterns
        """
        if not self.patterns_file.exists():
            return []

        patterns = []
        seen_ids = set()

        # Read all patterns (JSONL format)
        with open(self.patterns_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    pattern = json.loads(line)
                    pattern_id = pattern.get('id')

                    # Keep only the latest version of each pattern
                    if pattern_id and pattern_id not in seen_ids:
                        patterns.append(pattern)
                        seen_ids.add(pattern_id)
                except json.JSONDecodeError:
                    continue

        # Filter by status if specified
        if status:
            patterns = [p for p in patterns if p.get('status') == status]

        return patterns

    def update_pattern_status(self, pattern_id: str, status: str) -> bool:
        """
        Update pattern status.

        Args:
            pattern_id: Pattern ID
            status: New status (pending, suggested, accepted, rejected)

        Returns:
            True if successful
        """
        patterns = self.load_patterns()
        updated = False

        for pattern in patterns:
            if pattern.get('id') == pattern_id:
                pattern['status'] = status
                pattern['updated_at'] = datetime.now().isoformat()
                self.save_pattern(pattern)
                updated = True
                break

        return updated

    def save_config(self, config: Dict):
        """
        Save configuration.

        Args:
            config: Configuration dictionary
        """
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dumps(config, f, indent=2)

    def load_config(self) -> Dict:
        """
        Load configuration.

        Returns:
            Configuration dictionary
        """
        if not self.config_file.exists():
            self._init_default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Return default config if file is corrupted
            self._init_default_config()
            return self.load_config()

    def update_config(self, key: str, value) -> Dict:
        """
        Update a single configuration value.

        Args:
            key: Configuration key
            value: New value

        Returns:
            Updated configuration
        """
        config = self.load_config()
        config[key] = value
        self.save_config(config)
        return config

    def add_exclusion(self, exclusion_type: str, pattern: str):
        """
        Add an exclusion pattern.

        Args:
            exclusion_type: Type of exclusion (command, file, conversation)
            pattern: Pattern to exclude
        """
        config = self.load_config()
        exclusions = config.get('excluded_patterns', [])

        # Check if already excluded
        for exc in exclusions:
            if exc['type'] == exclusion_type and exc['pattern'] == pattern:
                return  # Already excluded

        # Add new exclusion
        exclusions.append({
            'type': exclusion_type,
            'pattern': pattern,
            'added_at': datetime.now().isoformat()
        })

        config['excluded_patterns'] = exclusions
        self.save_config(config)

    def remove_exclusion(self, exclusion_type: str, pattern: str) -> bool:
        """
        Remove an exclusion pattern.

        Args:
            exclusion_type: Type of exclusion
            pattern: Pattern to remove

        Returns:
            True if removed
        """
        config = self.load_config()
        exclusions = config.get('excluded_patterns', [])

        original_count = len(exclusions)
        exclusions = [
            exc for exc in exclusions
            if not (exc['type'] == exclusion_type and exc['pattern'] == pattern)
        ]

        if len(exclusions) < original_count:
            config['excluded_patterns'] = exclusions
            self.save_config(config)
            return True

        return False

    def reset_config(self):
        """Reset configuration to defaults."""
        self._init_default_config()

    def get_stats(self) -> Dict:
        """
        Get storage statistics.

        Returns:
            Dict with statistics
        """
        patterns = self.load_patterns()

        status_counts = {}
        for pattern in patterns:
            status = pattern.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            'total_patterns': len(patterns),
            'by_status': status_counts,
            'storage_path': str(self.storage_dir),
            'config_exists': self.config_file.exists()
        }


if __name__ == '__main__':
    # Example usage
    storage = PatternStorage()

    print("=== Storage Statistics ===")
    stats = storage.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n=== Configuration ===")
    config = storage.load_config()
    for key, value in config.items():
        print(f"{key}: {value}")
