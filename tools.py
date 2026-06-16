"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.
"""

import os
from dotenv import load_dotenv
from groq import Groq
from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to a .env file in the project root.")
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()

    # Step 1 — filter by price and size
    filtered = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None:
            if size.lower() not in item["size"].lower():
                continue
        filtered.append(item)

    # Step 2 — score by keyword overlap with description
    keywords = description.lower().split()

    def score(item):
        searchable = (
            item["title"].lower() + " " +
            item["description"].lower() + " " +
            " ".join(item["style_tags"]).lower() +
            " " + item["category"].lower()
        )
        return sum(1 for kw in keywords if kw in searchable)

    # Step 3 — drop zero scores, sort by score
    scored = [(item, score(item)) for item in filtered]
    scored = [(item, s) for item, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [item for item, _ in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()

    item_desc = (
        f"{new_item['title']} — {new_item['description']} "
        f"Colors: {', '.join(new_item['colors'])}. "
        f"Style: {', '.join(new_item['style_tags'])}."
    )

    # Empty wardrobe case
    if not wardrobe.get("items"):
        prompt = f"""A user is considering buying this thrifted item:
{item_desc}

They don't have a wardrobe entered yet. Give them 1-2 sentences of general styling 
advice — what kinds of pieces pair well with this item and what vibe it suits. 
Be specific and casual, not generic."""

    else:
        wardrobe_lines = []
        for w in wardrobe["items"]:
            note = f" ({w['notes']})" if w.get("notes") else ""
            wardrobe_lines.append(
                f"- {w['name']}: colors={', '.join(w['colors'])}, "
                f"style={', '.join(w['style_tags'])}{note}"
            )
        wardrobe_text = "\n".join(wardrobe_lines)

        prompt = f"""A user is considering buying this thrifted item:
{item_desc}

Their current wardrobe:
{wardrobe_text}

Suggest 1-2 specific outfit combinations using the new item and named pieces from 
their wardrobe. Mention the wardrobe pieces by name. Explain why the combination 
works (color, vibe, silhouette). Be casual and specific, not generic."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return "couldn't generate a fit card — outfit data was incomplete."

    client = _get_groq_client()

    prompt = f"""Write a 2-3 sentence Instagram/TikTok caption for this thrifted outfit.

Thrifted item: {new_item['title']}
Price: ${new_item['price']}
Platform: {new_item['platform']}
Outfit: {outfit}

Rules:
- Sound like a real person posting an OOTD, not a product description
- Mention the item name, price, and platform naturally (once each)
- Capture the specific vibe of the outfit
- Use casual language, maybe one emoji
- Do NOT use hashtags"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    return response.choices[0].message.content