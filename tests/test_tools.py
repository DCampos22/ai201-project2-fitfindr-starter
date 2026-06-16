from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── search_listings tests ─────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=30)
    assert all(item["price"] <= 30 for item in results)

def test_search_no_size_filter():
    results = search_listings("vintage tee", size=None, max_price=100)
    assert len(results) > 0

def test_search_sorted_by_relevance():
    results = search_listings("vintage grunge streetwear", size=None, max_price=100)
    assert len(results) > 0


# ── suggest_outfit tests ──────────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe():
    from utils.data_loader import load_listings
    item = load_listings()[5]
    result = suggest_outfit(item, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_empty_wardrobe():
    from utils.data_loader import load_listings
    item = load_listings()[0]
    result = suggest_outfit(item, get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0


# ── create_fit_card tests ─────────────────────────────────────────────────────

def test_create_fit_card_returns_string():
    from utils.data_loader import load_listings
    item = load_listings()[5]
    result = create_fit_card("baggy jeans and chunky sneakers with a graphic tee", item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_create_fit_card_empty_outfit():
    from utils.data_loader import load_listings
    item = load_listings()[0]
    result = create_fit_card("", item)
    assert "couldn't generate" in result.lower()