"""
Tests for SimilarityEngine - Sprint 2 Refactoring.

Tests cover:
    - Cosine similarity calculations
    - Euclidean and Manhattan distance
    - Vector normalization
    - Edge cases and error handling
"""

import pytest
import math
from vertice_core.agents.router.similarity import SimilarityEngine


class TestCosineSimilarity:
    """Test cosine similarity calculations."""

    def test_cosine_similarity_identical_vectors(self) -> None:
        """Test cosine similarity for identical vectors."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]

        similarity = SimilarityEngine.cosine_similarity(a, b)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal_vectors(self) -> None:
        """Test cosine similarity for orthogonal vectors."""
        a = [1.0, 0.0]
        b = [0.0, 1.0]

        similarity = SimilarityEngine.cosine_similarity(a, b)
        assert similarity == pytest.approx(0.0)

    def test_cosine_similarity_opposite_vectors(self) -> None:
        """Test cosine similarity for opposite vectors."""
        a = [1.0, 2.0]
        b = [-1.0, -2.0]

        similarity = SimilarityEngine.cosine_similarity(a, b)
        assert similarity == pytest.approx(-1.0)

    def test_cosine_similarity_partial_similarity(self) -> None:
        """Test cosine similarity for partially similar vectors."""
        a = [1.0, 2.0, 3.0]
        b = [2.0, 3.0, 4.0]

        similarity = SimilarityEngine.cosine_similarity(a, b)
        # Should be high but not perfect
        assert 0.95 < similarity < 1.0

    def test_cosine_similarity_different_lengths(self) -> None:
        """Test cosine similarity for vectors of different lengths."""
        a = [1.0, 2.0]
        b = [1.0, 2.0, 3.0]

        similarity = SimilarityEngine.cosine_similarity(a, b)
        assert similarity == 0.0

    def test_cosine_similarity_empty_vectors(self) -> None:
        """Test cosine similarity for empty vectors."""
        a = []
        b = []

        similarity = SimilarityEngine.cosine_similarity(a, b)
        assert similarity == 0.0

    def test_cosine_similarity_zero_vector(self) -> None:
        """Test cosine similarity with zero vector."""
        a = [0.0, 0.0]
        b = [1.0, 1.0]

        similarity = SimilarityEngine.cosine_similarity(a, b)
        assert similarity == 0.0


class TestEuclideanDistance:
    """Test Euclidean distance calculations."""

    def test_euclidean_distance_identical_vectors(self) -> None:
        """Test Euclidean distance for identical vectors."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]

        distance = SimilarityEngine.euclidean_distance(a, b)
        assert distance == pytest.approx(0.0)

    def test_euclidean_distance_simple_case(self) -> None:
        """Test Euclidean distance for simple case."""
        a = [0.0, 0.0]
        b = [3.0, 4.0]

        distance = SimilarityEngine.euclidean_distance(a, b)
        assert distance == pytest.approx(5.0)  # 3-4-5 triangle

    def test_euclidean_distance_partial_difference(self) -> None:
        """Test Euclidean distance with partial differences."""
        a = [1.0, 1.0, 1.0]
        b = [2.0, 2.0, 2.0]

        distance = SimilarityEngine.euclidean_distance(a, b)
        expected = math.sqrt(3)  # sqrt(1^2 + 1^2 + 1^2)
        assert distance == pytest.approx(expected)

    def test_euclidean_distance_different_lengths(self) -> None:
        """Test Euclidean distance for vectors of different lengths."""
        a = [1.0, 2.0]
        b = [1.0, 2.0, 3.0]

        distance = SimilarityEngine.euclidean_distance(a, b)
        assert distance > 1000  # Returns large value for different lengths

    def test_euclidean_distance_empty_vectors(self) -> None:
        """Test Euclidean distance for empty vectors."""
        a = []
        b = []

        distance = SimilarityEngine.euclidean_distance(a, b)
        assert distance == 0.0


class TestManhattanDistance:
    """Test Manhattan distance calculations."""

    def test_manhattan_distance_identical_vectors(self) -> None:
        """Test Manhattan distance for identical vectors."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]

        distance = SimilarityEngine.manhattan_distance(a, b)
        assert distance == pytest.approx(0.0)

    def test_manhattan_distance_simple_case(self) -> None:
        """Test Manhattan distance for simple case."""
        a = [0.0, 0.0]
        b = [3.0, 4.0]

        distance = SimilarityEngine.manhattan_distance(a, b)
        assert distance == pytest.approx(7.0)  # |3| + |4|

    def test_manhattan_distance_mixed_directions(self) -> None:
        """Test Manhattan distance with positive and negative differences."""
        a = [1.0, 2.0, 3.0]
        b = [4.0, 0.0, 5.0]

        distance = SimilarityEngine.manhattan_distance(a, b)
        expected = abs(4 - 1) + abs(0 - 2) + abs(5 - 3)  # 3 + 2 + 2 = 7
        assert distance == pytest.approx(expected)

    def test_manhattan_distance_different_lengths(self) -> None:
        """Test Manhattan distance for vectors of different lengths."""
        a = [1.0, 2.0]
        b = [1.0, 2.0, 3.0]

        distance = SimilarityEngine.manhattan_distance(a, b)
        assert distance > 1000  # Returns large value for different lengths

    def test_manhattan_distance_empty_vectors(self) -> None:
        """Test Manhattan distance for empty vectors."""
        a = []
        b = []

        distance = SimilarityEngine.manhattan_distance(a, b)
        assert distance == 0.0


class TestVectorNormalization:
    """Test vector normalization."""

    def test_normalize_vector_simple_case(self) -> None:
        """Test vector normalization for simple case."""
        vector = [3.0, 4.0]

        normalized = SimilarityEngine.normalize_vector(vector)
        expected_magnitude = math.sqrt(3**2 + 4**2)  # 5.0
        expected = [3.0 / 5.0, 4.0 / 5.0]

        assert normalized == pytest.approx(expected)

    def test_normalize_vector_already_normalized(self) -> None:
        """Test normalization of already normalized vector."""
        vector = [1.0, 0.0]

        normalized = SimilarityEngine.normalize_vector(vector)
        assert normalized == pytest.approx([1.0, 0.0])

    def test_normalize_vector_zero_vector(self) -> None:
        """Test normalization of zero vector."""
        vector = [0.0, 0.0, 0.0]

        normalized = SimilarityEngine.normalize_vector(vector)
        assert normalized == [0.0, 0.0, 0.0]

    def test_normalize_vector_negative_values(self) -> None:
        """Test normalization with negative values."""
        vector = [-3.0, 4.0]

        normalized = SimilarityEngine.normalize_vector(vector)
        magnitude = math.sqrt((-3) ** 2 + 4**2)  # 5.0
        expected = [-3.0 / 5.0, 4.0 / 5.0]

        assert normalized == pytest.approx(expected)

    def test_normalize_vector_single_element(self) -> None:
        """Test normalization of single element vector."""
        vector = [5.0]

        normalized = SimilarityEngine.normalize_vector(vector)
        assert normalized == pytest.approx([1.0])

    def test_normalize_vector_large_values(self) -> None:
        """Test normalization with large values."""
        vector = [100.0, 200.0]

        normalized = SimilarityEngine.normalize_vector(vector)
        magnitude = math.sqrt(100**2 + 200**2)
        expected = [100.0 / magnitude, 200.0 / magnitude]

        assert normalized == pytest.approx(expected)


class TestSimilarityEngineEdgeCases:
    """Test edge cases and error conditions."""

    def test_cosine_similarity_none_vectors(self) -> None:
        """Test cosine similarity with None vectors."""
        similarity = SimilarityEngine.cosine_similarity(None, None)  # type: ignore
        assert similarity == 0.0

    def test_distance_none_vectors(self) -> None:
        """Test distance functions with None vectors."""
        # These should raise TypeError for None inputs
        with pytest.raises(TypeError):
            SimilarityEngine.euclidean_distance(None, None)  # type: ignore

        with pytest.raises(TypeError):
            SimilarityEngine.manhattan_distance(None, None)  # type: ignore

    def test_normalize_none_vector(self) -> None:
        """Test normalization with None vector."""
        with pytest.raises(TypeError):
            SimilarityEngine.normalize_vector(None)  # type: ignore

    def test_cosine_similarity_precision(self) -> None:
        """Test cosine similarity precision with floating point values."""
        a = [1.0000000001, 2.0000000001]
        b = [1.0, 2.0]

        similarity = SimilarityEngine.cosine_similarity(a, b)
        # Should be very close to 1.0
        assert similarity > 0.999999
