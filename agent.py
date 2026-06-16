"""
agent.py
The FitFindr planning loop.
"""

import re
from tools import search_listings, suggest_outfit, create_fit_card


def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """Extract description, size, and max_price from natural language query."""
    parsed = {"description": query, "size": None, "max_price": None}

    # Extract price — looks for "under $30", "$30", "30 dollars"
    price_match = re.search(r"under\s*\$?(\d+(?:\.\d+)?)", query, re.IGNORECASE)
    if not price_match:
        price_match = re.search(r"\$(\d+(?:\.\d+)?)", query, re.IGNORECASE)
    if price_match:
        parsed["max_price"] = float(price_match.group(1))

    # Extract size — looks for "size M", "size XL", "size S/M", "W30"
    size_match = re.search(
        r"\bsize\s+([A-Z0-9/]+)\b|\b(XS|S|M|L|XL|XXL|S\/M|M\/L|W\d+)\b",
        query, re.IGNORECASE
    )
    if size_match:
        parsed["size"] = (size_match.group(1) or size_match.group(2)).upper()

    # Clean size and price mentions from description
    description = query
    description = re.sub(r"under\s*\$?\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\$\d+(?:\.\d+)?", "", description)
    description = re.sub(r"\bsize\s+[A-Z0-9/]+\b", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\s+", " ", description).strip()
    parsed["description"] = description

    return parsed


def run_agent(query: str, wardrobe: dict) -> dict:
    # Step 1 — initialize session
    session = _new_session(query, wardrobe)

    # Step 2 — parse query
    session["parsed"] = _parse_query(query)
    print(f"Parsed: {session['parsed']}")

    # Step 3 — search listings
    results = search_listings(
        description=session["parsed"]["description"],
        size=session["parsed"]["size"],
        max_price=session["parsed"]["max_price"],
    )
    session["search_results"] = results

    if not results:
        session["error"] = (
            "I couldn't find any listings matching your search. "
            "Try broadening your description, adjusting your size, or raising your price limit."
        )
        return session

    # Step 4 — select top result
    session["selected_item"] = results[0]
    print(f"Selected: {session['selected_item']['title']}")

    # Step 5 — suggest outfit
    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )
    print(f"Outfit suggestion generated.")

    # Step 6 — create fit card
    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )
    print(f"Fit card generated.")

    # Step 7 — return session
    return session


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")