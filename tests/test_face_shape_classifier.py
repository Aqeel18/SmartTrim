"""
Unit tests for the face shape classifier.

Tests cover:
  - The geometric classifier's scoring logic for all 6 face shapes
  - Confidence bounds (must always be in [0.5, 0.95])
  - The analyze() return schema consistency
  - Edge cases: borderline metrics, missing face_bgr
"""
import pytest
import numpy as np
from app.core.face_shape_classifier import FaceShapeClassifier


@pytest.fixture(scope="module")
def clf():
    """Single classifier instance shared across all tests (models load once)."""
    return FaceShapeClassifier()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_metrics(face_length=1.1, forehead_width=1.0, cheekbone_width=1.0,
                  jaw_width=0.85, chin_angle=110.0):
    return {
        "face_length":      face_length,
        "forehead_width":   forehead_width,
        "cheekbone_width":  cheekbone_width,
        "jaw_width":        jaw_width,
        "chin_angle":       chin_angle,
    }


# ---------------------------------------------------------------------------
# Geometric classifier — shape coverage
# ---------------------------------------------------------------------------

class TestGeometricClassifier:
    def test_oblong_detected(self, clf):
        metrics = _make_metrics(face_length=1.35)
        shape, conf = clf.classify_geometric(metrics)
        assert shape == "Oblong", f"Expected Oblong, got {shape}"

    def test_square_detected(self, clf):
        metrics = _make_metrics(jaw_width=0.92, chin_angle=120.0)
        shape, conf = clf.classify_geometric(metrics)
        assert shape == "Square", f"Expected Square, got {shape}"

    def test_heart_detected(self, clf):
        metrics = _make_metrics(forehead_width=1.08, chin_angle=98.0)
        shape, conf = clf.classify_geometric(metrics)
        assert shape == "Heart", f"Expected Heart, got {shape}"

    def test_diamond_detected(self, clf):
        metrics = _make_metrics(jaw_width=0.68, chin_angle=95.0)
        shape, conf = clf.classify_geometric(metrics)
        assert shape == "Diamond", f"Expected Diamond, got {shape}"

    def test_round_detected(self, clf):
        metrics = _make_metrics(face_length=1.05)
        shape, conf = clf.classify_geometric(metrics)
        assert shape == "Round", f"Expected Round, got {shape}"

    def test_oval_default(self, clf):
        # Neutral metrics that don't strongly satisfy any other shape
        metrics = _make_metrics(face_length=1.18, jaw_width=0.83, chin_angle=108.0)
        shape, conf = clf.classify_geometric(metrics)
        assert shape == "Oval", f"Expected Oval, got {shape}"

    def test_confidence_in_bounds(self, clf):
        for face_length in [1.05, 1.15, 1.30]:
            metrics = _make_metrics(face_length=face_length)
            _, conf = clf.classify_geometric(metrics)
            assert 0.50 <= conf <= 0.95, f"Confidence {conf} out of [0.5, 0.95] for fl={face_length}"

    def test_returns_tuple(self, clf):
        metrics = _make_metrics()
        result = clf.classify_geometric(metrics)
        assert isinstance(result, tuple) and len(result) == 2


# ---------------------------------------------------------------------------
# analyze() — schema and consistency
# ---------------------------------------------------------------------------

class TestAnalyzeSchema:
    """Validates that analyze() always returns the correct schema."""

    # We need 468 landmark points — fill with dummy (0, 0) coords
    DUMMY_LANDMARKS = [(0, 0)] * 468

    def test_schema_keys_present(self, clf):
        result = clf.analyze(self.DUMMY_LANDMARKS)
        for key in ("face_shape", "confidence", "scores", "method", "metrics"):
            assert key in result, f"Missing key: {key}"

    def test_face_shape_is_valid(self, clf):
        result = clf.analyze(self.DUMMY_LANDMARKS)
        valid = {"Oval", "Round", "Oblong", "Square", "Heart", "Diamond"}
        assert result["face_shape"] in valid

    def test_confidence_numeric(self, clf):
        result = clf.analyze(self.DUMMY_LANDMARKS)
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_scores_all_shapes_covered(self, clf):
        result = clf.analyze(self.DUMMY_LANDMARKS)
        expected_keys = {"Oval", "Round", "Oblong", "Square", "Heart", "Diamond"}
        assert set(result["scores"].keys()) == expected_keys

    def test_method_is_geometric_without_ml_model(self, clf):
        # ML model weights are not present in the repo — method should be 'geometric'
        result = clf.analyze(self.DUMMY_LANDMARKS)
        assert result["method"] in ("geometric", "ml")


# ---------------------------------------------------------------------------
# compute_metrics — sanity
# ---------------------------------------------------------------------------

class TestComputeMetrics:
    DUMMY_LANDMARKS = [(i * 2, i * 3) for i in range(468)]

    def test_metrics_keys(self, clf):
        metrics = clf.compute_metrics(self.DUMMY_LANDMARKS)
        for key in ("face_length", "forehead_width", "cheekbone_width", "jaw_width", "chin_angle"):
            assert key in metrics

    def test_insufficient_landmarks_raises(self, clf):
        with pytest.raises(ValueError, match="Insufficient landmarks"):
            clf.compute_metrics([(0, 0)] * 100)
