#!/usr/bin/env python3
"""Shared constants for pattern detection."""

# Bash command prefixes for command detection
BASH_INDICATORS = [
    'npm ', 'git ', 'python ', 'node ', 'yarn ', 'pnpm ',
    'cd ', 'ls ', 'cat ', 'grep ', 'find ', 'sed ', 'awk ',
    'mkdir ', 'rm ', 'cp ', 'mv ', 'touch ', 'chmod ',
    'docker ', 'kubectl ', 'cargo ', 'go ', 'rustc ',
]

# English stop words for text analysis
ENGLISH_STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
    'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
    'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
    'me', 'him', 'her', 'us', 'them', 'please', 'make',
}

# Japanese stop words (romanized and native)
JAPANESE_STOP_WORDS = {
    'no', 'ni', 'wo', 'ga', 'wa', 'de', 'ka', 'ne', 'yo', 'na',
    'してください', 'して', 'を', 'の', 'に', 'が', 'は', 'で'
}

# Combined stop words set
STOP_WORDS = ENGLISH_STOP_WORDS | JAPANESE_STOP_WORDS
