"""
Similarity Engine - Cosine similarity and vector operations.
"""

import math
from typing import List


class SimilarityEngine:
    """Engine for computing vector similarities."""

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Similarity score between 0 and 1
        """
        if not a or not b or len(a) != len(b):
            return 0.0

        # Compute dot product
        dot_product = sum(x * y for x, y in zip(a, b))

        # Compute magnitudes
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(y * y for y in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    @staticmethod
    def euclidean_distance(a: List[float], b: List[float]) -> float:
        """
        Compute Euclidean distance between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Distance (smaller = more similar)
        """
        if len(a) != len(b):
            return float("inf")

        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    @staticmethod
    def manhattan_distance(a: List[float], b: List[float]) -> float:
        """
        Compute Manhattan distance between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Distance (smaller = more similar)
        """
        if len(a) != len(b):
            return float("inf")

        return sum(abs(x - y) for x, y in zip(a, b))

    @staticmethod
    def normalize_vector(vector: List[float]) -> List[float]:
        """
        Normalize a vector to unit length.

        Args:
            vector: Input vector

        Returns:
            Normalized vector
        """
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude == 0:
            return vector
        return [x / magnitude for x in vector]
