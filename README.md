# FitFindr — Starter Kit

An AI agent that helps you find secondhand pieces and figure out how to wear them. Describe what you're looking for in natural language. FitFindr searches mock thrift listings, suggests outfits using your existing wardrobe, and generates a shareable caption for the look.

## What's Included

```
ai201-project2-fitfindr-starter/

├── data/

│   ├── listings.json          # 40 mock secondhand listings

│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe

├── utils/

│   └── data_loader.py         # Helper functions for loading the data

├── tools.py                   # Three agent tools: search, outfit, fit card

├── agent.py                   # Planning loop and session state

├── app.py                     # Gradio web interface

├── tests/

│   └── test_tools.py          # pytest tests for all three tools

├── planning.md                # Agent design spec

└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```
Run the app:
```bash
python app.py
```

Open http://localhost:7860 in your browser.

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## How It Works

FitFindr is an agent, not just a search tool. It orchestrates three tools in sequence and makes decisions based on what each tool returns. If a search returns no results, the agent stops and tells you what to adjust, it does not call the outfit or caption tools with empty input.

## Tools

### search_listings(description, size, max_price)
Searches the mock listings dataset for items matching the user's request.
- `description` (str): Natural language description (e.g. "vintage graphic tee")
- `size` (str or None): Size filter — case-insensitive partial match
- `max_price` (float or None): Price ceiling, inclusive

Returns a list of matching listing dicts sorted by relevance. Returns `[]` if nothing matches, never raises an exception.

Load listings directly with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

### suggest_outfit(new_item, wardrobe)
Given a thrifted item and the user's wardrobe, suggests 1–2 complete outfit combinations using named wardrobe pieces.
- `new_item` (dict): A listing dict from search_listings
- `wardrobe` (dict): Wardrobe dict with an "items" key

Returns a string with specific outfit suggestions. If the wardrobe is empty, returns general styling advice instead of crashing.

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

### create_fit_card(outfit, new_item)
Generates a casual, shareable social media caption for the outfit.
- `outfit` (str): Outfit suggestion string from suggest_outfit
- `new_item` (dict): Listing dict for the thrifted item

Returns a 2–3 sentence caption in a casual first-person voice. If outfit is empty, returns a descriptive error message string instead of crashing.

## Planning Loop

The agent runs sequentially with a conditional check after each step:

1. Parse the query with regex to extract description, size, and max_price
2. Call search_listings() — if empty, return error message and stop
3. Call suggest_outfit() with the top result and wardrobe
4. Call create_fit_card() with the outfit suggestion
5. Return the completed session

The agent never calls all three tools unconditionally, the search result controls whether the rest of the pipeline runs.

## State Management

All data is stored in a session dict passed between tools:

- `session["selected_item"]` — top search result, passed into suggest_outfit
- `session["outfit_suggestion"]` — string from suggest_outfit, passed into create_fit_card
- `session["fit_card"]` — final caption string
- `session["error"]` — set if any step fails, triggers early return

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match | "I couldn't find any listings matching your search. Try broadening your description, adjusting your size, or raising your price limit." |
| suggest_outfit | Empty wardrobe | General styling advice for the item — pipeline continues |
| create_fit_card | Empty outfit string | "couldn't generate a fit card — outfit data was incomplete." |

## Running Tests

```bash
python -m pytest tests/
```

## AI Usage

**Instance 1 — search_listings implementation**
- *Input to AI:* Tool 1 spec from planning.md (inputs, return value, failure mode) plus listings field definitions
- *Produced:* search_listings() with price/size filtering and keyword scoring
- *Changed:* Switched size matching from exact to case-insensitive partial match so "M" correctly matches "S/M"

**Instance 2 — planning loop implementation**
- *Input to AI:* Planning Loop + State Management sections and Architecture diagram from planning.md
- *Produced:* Full run_agent() with session dict and conditional branching
- *Changed:* Switched query parsing from LLM call to regex, faster and no extra API call needed for this dataset
