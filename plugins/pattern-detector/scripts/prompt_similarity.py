#!/usr/bin/env python3
"""Prompt similarity detection for finding repeated user instructions."""

import re
from typing import List, Tuple, Set, Dict
from difflib import SequenceMatcher

from constants import STOP_WORDS


class PromptSimilarity:
    """Detects similar prompts using various text similarity algorithms."""

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize prompt similarity detector.

        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider prompts similar
        """
        self.similarity_threshold = similarity_threshold

    def normalize_prompt(self, prompt: str) -> str:
        """
        Normalize a prompt for comparison.

        Args:
            prompt: Raw prompt text

        Returns:
            Normalized prompt text
        """
        # Convert to lowercase
        text = prompt.lower()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common filler words (optional - keep domain-specific words)
        # We'll keep most words to preserve meaning

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def extract_keywords(self, prompt: str) -> Set[str]:
        """
        Extract keywords from a prompt.

        Args:
            prompt: Normalized prompt text

        Returns:
            Set of keywords
        """
        # Split into words
        words = re.findall(r'\b\w+\b', prompt)

        # Filter out common stop words
        keywords = {word for word in words if word not in STOP_WORDS and len(word) > 2}

        return keywords

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """
        Calculate Jaccard similarity between two sets.

        Args:
            set1: First set of keywords
            set2: Second set of keywords

        Returns:
            Similarity score (0-1)
        """
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def sequence_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate sequence similarity using SequenceMatcher.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def calculate_similarity(self, prompt1: str, prompt2: str) -> float:
        """
        Calculate overall similarity between two prompts.

        Args:
            prompt1: First prompt
            prompt2: Second prompt

        Returns:
            Similarity score (0-1)
        """
        # Normalize prompts
        norm1 = self.normalize_prompt(prompt1)
        norm2 = self.normalize_prompt(prompt2)

        # If prompts are identical after normalization
        if norm1 == norm2:
            return 1.0

        # Extract keywords
        keywords1 = self.extract_keywords(norm1)
        keywords2 = self.extract_keywords(norm2)

        # Calculate keyword similarity (Jaccard)
        keyword_sim = self.jaccard_similarity(keywords1, keywords2)

        # Calculate sequence similarity
        sequence_sim = self.sequence_similarity(norm1, norm2)

        # Weighted average (keyword similarity is more important for semantic meaning)
        # 60% keyword similarity, 40% sequence similarity
        overall_sim = (keyword_sim * 0.6) + (sequence_sim * 0.4)

        return overall_sim

    def is_similar(self, prompt1: str, prompt2: str) -> bool:
        """
        Check if two prompts are similar.

        Args:
            prompt1: First prompt
            prompt2: Second prompt

        Returns:
            True if prompts are similar, False otherwise
        """
        similarity = self.calculate_similarity(prompt1, prompt2)
        return similarity >= self.similarity_threshold

    def find_similar_prompts(
        self,
        prompts: List[str],
        min_cluster_size: int = 2
    ) -> List[Tuple[str, List[int], float]]:
        """
        Find clusters of similar prompts.

        Args:
            prompts: List of prompt texts
            min_cluster_size: Minimum size of a cluster to include

        Returns:
            List of tuples (representative_prompt, indices, avg_similarity)
        """
        if not prompts:
            return []

        # Pre-compute normalized prompts and keywords for efficiency
        normalized = [self.normalize_prompt(p) for p in prompts]
        keywords_cache = [self.extract_keywords(norm) for norm in normalized]

        # Track which prompts have been clustered
        clustered = set()
        clusters = []

        for i in range(len(prompts)):
            if i in clustered:
                continue

            # Start a new cluster with this prompt
            cluster_indices = [i]
            similarities = []

            # Find all similar prompts
            for j in range(i + 1, len(prompts)):
                if j in clustered:
                    continue

                # Calculate similarity using cached values
                similarity = self._calculate_similarity_cached(
                    normalized[i], normalized[j],
                    keywords_cache[i], keywords_cache[j]
                )

                if similarity >= self.similarity_threshold:
                    cluster_indices.append(j)
                    similarities.append(similarity)
                    clustered.add(j)

            # Only include clusters with enough members
            if len(cluster_indices) >= min_cluster_size:
                clustered.add(i)
                avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0
                clusters.append((prompts[i], cluster_indices, avg_similarity))

        return clusters

    def _calculate_similarity_cached(
        self,
        norm1: str,
        norm2: str,
        keywords1: Set[str],
        keywords2: Set[str]
    ) -> float:
        """
        Calculate similarity using pre-computed normalized text and keywords.

        Args:
            norm1: Pre-normalized first text
            norm2: Pre-normalized second text
            keywords1: Pre-extracted keywords from first text
            keywords2: Pre-extracted keywords from second text

        Returns:
            Similarity score (0-1)
        """
        # If prompts are identical after normalization
        if norm1 == norm2:
            return 1.0

        # Calculate keyword similarity (Jaccard)
        keyword_sim = self.jaccard_similarity(keywords1, keywords2)

        # Calculate sequence similarity
        sequence_sim = self.sequence_similarity(norm1, norm2)

        # Weighted average (keyword similarity is more important for semantic meaning)
        # 60% keyword similarity, 40% sequence similarity
        overall_sim = (keyword_sim * 0.6) + (sequence_sim * 0.4)

        return overall_sim

    def extract_common_pattern(self, prompts: List[str]) -> str:
        """
        Extract a common pattern from a list of similar prompts.

        Args:
            prompts: List of similar prompt texts

        Returns:
            Representative pattern or first prompt
        """
        if not prompts:
            return ""

        if len(prompts) == 1:
            return prompts[0]

        # Find the shortest prompt as it's likely the most concise
        representative = min(prompts, key=len)

        return representative


if __name__ == '__main__':
    # Example usage
    detector = PromptSimilarity(similarity_threshold=0.7)

    # Test prompts
    test_prompts = [
        "テストを実行してください",
        "テストを実行して",
        "Run the tests",
        "Run tests",
        "コミットしてください",
        "git commit してください",
        "Please commit the changes",
    ]

    print("=== Prompt Similarity Detection ===\n")

    # Test pairwise similarity
    print("Pairwise Similarities:")
    for i, p1 in enumerate(test_prompts):
        for j, p2 in enumerate(test_prompts):
            if j > i:
                sim = detector.calculate_similarity(p1, p2)
                if sim > 0.5:
                    print(f"{sim:.2f}: '{p1}' <-> '{p2}'")

    print("\n=== Clusters ===")
    clusters = detector.find_similar_prompts(test_prompts, min_cluster_size=2)
    for i, (rep, indices, avg_sim) in enumerate(clusters, 1):
        print(f"\nCluster {i} (avg similarity: {avg_sim:.2f}):")
        print(f"  Representative: '{rep}'")
        print(f"  Members ({len(indices)}):")
        for idx in indices:
            print(f"    - '{test_prompts[idx]}'")
