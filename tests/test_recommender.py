"""
Unit tests for the hairstyle recommender.
"""
import pytest
from app.core.hairstyle_recommender import HairstyleRecommender

AVAILABLE = [
    "men/quiff.png",
    "men/pompadour.png",
    "men/texturedcrop.png",
    "men/sidepart.png",
    "men/taper-fade.png",
    "men/bowl-cut-men-wavy.png",
    "men/side-part-curtain-hairstyle-men.png",
    "men/faux hawk.png",
    "men/ivy-league-haircut-men.png",
    "men/mid-length-layered-haircut.png",
    "men/Slick_Back.png",
    "men/Crew-Cut-Haircut-Men.png",
]


@pytest.fixture(scope="module")
def recommender():
    return HairstyleRecommender()


class TestRecommend:
    @pytest.mark.parametrize("shape", ["Oval", "Round", "Square", "Heart", "Oblong", "Diamond"])
    def test_returns_list_for_all_shapes(self, recommender, shape):
        result = recommender.recommend(shape, AVAILABLE)
        assert isinstance(result, list)

    @pytest.mark.parametrize("shape", ["Oval", "Round", "Square", "Heart", "Oblong", "Diamond"])
    def test_all_results_in_available(self, recommender, shape):
        result = recommender.recommend(shape, AVAILABLE)
        for item in result:
            assert item in AVAILABLE, f"{item} not in available styles"

    def test_unknown_shape_returns_empty(self, recommender):
        result = recommender.recommend("Alien", AVAILABLE)
        assert result == []

    def test_empty_available_returns_empty(self, recommender):
        result = recommender.recommend("Oval", [])
        assert result == []


class TestRecommendWithReasons:
    def test_returns_tuple(self, recommender):
        recs, reasons = recommender.recommend_with_reasons("Oval", AVAILABLE)
        assert isinstance(recs, list)
        assert isinstance(reasons, dict)

    def test_reasons_cover_all_recommendations(self, recommender):
        recs, reasons = recommender.recommend_with_reasons("Round", AVAILABLE)
        for item in recs:
            assert item in reasons, f"No reason for {item}"

    def test_reasons_are_non_empty_strings(self, recommender):
        _, reasons = recommender.recommend_with_reasons("Square", AVAILABLE)
        for val, reason in reasons.items():
            assert isinstance(reason, str) and len(reason) > 0
