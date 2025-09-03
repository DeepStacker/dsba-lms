import pytest
from app.core.calculations import get_grade_point_from_marks, get_score_distribution, GRADE_BANDS


class TestGradeCalculations:
    """Test cases for grade calculation functions."""

    def test_get_grade_point_from_marks_perfect_score(self):
        """Test grade point calculation for perfect score (100%)."""
        result = get_grade_point_from_marks(100, 100)
        assert result == GRADE_BANDS["O"]

    def test_get_grade_point_from_marks_high_score(self):
        """Test grade point calculation for high score (95%)."""
        result = get_grade_point_from_marks(95, 100)
        assert result == GRADE_BANDS["O"]

    def test_get_grade_point_from_marks_a_plus_range(self):
        """Test grade point calculation for A+ range (90-94%)."""
        result = get_grade_point_from_marks(90, 100)
        assert result == GRADE_BANDS["A+"]

        result = get_grade_point_from_marks(94, 100)
        assert result == GRADE_BANDS["A+"]

    def test_get_grade_point_from_marks_a_range(self):
        """Test grade point calculation for A range (85-89%)."""
        result = get_grade_point_from_marks(85, 100)
        assert result == GRADE_BANDS["A"]

        result = get_grade_point_from_marks(89, 100)
        assert result == GRADE_BANDS["A"]

    def test_get_grade_point_from_marks_b_plus_range(self):
        """Test grade point calculation for B+ range (80-84%)."""
        result = get_grade_point_from_marks(80, 100)
        assert result == GRADE_BANDS["B+"]

        result = get_grade_point_from_marks(84, 100)
        assert result == GRADE_BANDS["B+"]

    def test_get_grade_point_from_marks_b_range(self):
        """Test grade point calculation for B range (75-79%)."""
        result = get_grade_point_from_marks(75, 100)
        assert result == GRADE_BANDS["B"]

        result = get_grade_point_from_marks(79, 100)
        assert result == GRADE_BANDS["B"]

    def test_get_grade_point_from_marks_c_plus_range(self):
        """Test grade point calculation for C+ range (70-74%)."""
        result = get_grade_point_from_marks(70, 100)
        assert result == GRADE_BANDS["C+"]

        result = get_grade_point_from_marks(74, 100)
        assert result == GRADE_BANDS["C+"]

    def test_get_grade_point_from_marks_c_range(self):
        """Test grade point calculation for C range (60-69%)."""
        result = get_grade_point_from_marks(60, 100)
        assert result == GRADE_BANDS["C"]

        result = get_grade_point_from_marks(69, 100)
        assert result == GRADE_BANDS["C"]

    def test_get_grade_point_from_marks_d_range(self):
        """Test grade point calculation for D range (40-59%)."""
        result = get_grade_point_from_marks(40, 100)
        assert result == GRADE_BANDS["D"]

        result = get_grade_point_from_marks(59, 100)
        assert result == GRADE_BANDS["D"]

    def test_get_grade_point_from_marks_fail_range(self):
        """Test grade point calculation for failing range (<40%)."""
        result = get_grade_point_from_marks(39, 100)
        assert result == GRADE_BANDS["F"]

        result = get_grade_point_from_marks(0, 100)
        assert result == GRADE_BANDS["F"]

    def test_get_grade_point_from_marks_division_by_zero(self):
        """Test grade point calculation with zero max marks."""
        result = get_grade_point_from_marks(50, 0)
        assert result == 0

    def test_get_grade_point_from_marks_negative_values(self):
        """Test grade point calculation with negative values."""
        result = get_grade_point_from_marks(-10, 100)
        assert result == GRADE_BANDS["F"]

    def test_get_grade_point_from_marks_partial_scores(self):
        """Test grade point calculation for partial marks."""
        result = get_grade_point_from_marks(85.5, 100)
        assert result == GRADE_BANDS["A"]

        result = get_grade_point_from_marks(75.5, 100)
        assert result == GRADE_BANDS["B"]


class TestScoreDistribution:
    """Test cases for score distribution function."""

    def test_get_score_distribution_empty_list(self):
        """Test score distribution with empty list."""
        result = get_score_distribution([])
        assert result == {}

    def test_get_score_distribution_single_score(self):
        """Test score distribution with single score."""
        result = get_score_distribution([85.0])
        assert len(result) == 1

    def test_get_score_distribution_normal_distribution(self):
        """Test score distribution with normal data."""
        scores = [60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 70.0, 75.0, 80.0, 85.0]
        result = get_score_distribution(scores)
        assert len(result) > 0
        assert sum(result.values()) == len(scores)

    def test_get_score_distribution_identical_scores(self):
        """Test score distribution with identical scores."""
        scores = [80.0] * 10
        result = get_score_distribution(scores)
        assert len(result) == 1

    def test_get_score_distribution_wide_range(self):
        """Test score distribution with wide score range."""
        scores = [0.0, 25.0, 50.0, 75.0, 100.0]
        result = get_score_distribution(scores)
        assert len(result) > 0

    def test_get_score_distribution_small_range(self):
        """Test score distribution with small score range."""
        scores = [79.0, 80.0, 81.0, 80.0, 81.0]
        result = get_score_distribution(scores)
        assert len(result) > 0


class TestGradeBands:
    """Test cases for grade bands constants."""

    def test_grade_bands_structure(self):
        """Test that GRADE_BANDS has expected structure."""
        assert isinstance(GRADE_BANDS, dict)
        assert len(GRADE_BANDS) == 9  # O, A+, A, B+, B, C+, C, D, F

    def test_grade_bands_values(self):
        """Test that GRADE_BANDS has expected values."""
        assert GRADE_BANDS["O"] == 10.0
        assert GRADE_BANDS["A+"] == 9.0
        assert GRADE_BANDS["A"] == 8.0
        assert GRADE_BANDS["B+"] == 7.5
        assert GRADE_BANDS["B"] == 7.0
        assert GRADE_BANDS["C+"] == 6.5
        assert GRADE_BANDS["C"] == 6.0
        assert GRADE_BANDS["D"] == 4.0
        assert GRADE_BANDS["F"] == 0.0

    def test_grade_bands_ordering(self):
        """Test that grade band values are in descending order."""
        grades = list(GRADE_BANDS.values())
        assert grades == sorted(grades, reverse=True)
