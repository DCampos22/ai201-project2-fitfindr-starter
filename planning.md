# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Searches the mock listings dataset and returns items that match the user's description, size, and price ceiling. Matching is done against title, description, style_tags, and category fields.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): A natural language description of the item the user wants (e.g. "vintage graphic tee", "baggy jeans"). Used to match against title, description, and style_tags.
- `size` (str): The user's size (e.g. "M", "S/M", "W30"). Matched against the listing's size field.
- `max_price` (float): The maximum price the user is willing to pay. Filters out any listing with price above this value.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of matching listing dictionaries, each containing: id, title, description, category, style_tags, size, condition, price, colors, brand, and platform. The list is sorted by relevance (style_tag overlap with description). Returns an empty list if nothing matches.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
The agent stops the pipeline and returns the message: "I couldn't find any listings matching your search. Try broadening your description, adjusting your size, or raising your price limit." No further tools are called.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a specific listing item and the user's wardrobe, uses an LLM to suggest one or more complete outfit combinations that incorporate the new item with existing wardrobe pieces.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A single listing dictionary returned by search_listings — contains title, category, colors, style_tags, description.
- `wardrobe` (dict): A wardrobe dictionary with an "items" key containing a list of wardrobe item dicts. Each wardrobe item has: id, name, category, colors, style_tags, notes.

**What it returns:**
<!-- Describe the return value -->
A string containing 1–2 outfit suggestions written in natural language. Each suggestion names specific wardrobe pieces by name and explains why they work together (color,style, vibe).

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty (items list has length 0), the agent skips outfit matching and returns: "Your wardrobe is empty, I can't suggest a full outfit yet, but this piece would work well as a starting point. Add some basics to get outfit suggestions." If the LLM call fails, the agent returns: "I wasn't able to generate outfit suggestions right now. Here's the item I found: [item title]."

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generates a short, shareable social media caption describing the complete outfit, the kind of thing someone would caption an Instagram or TikTok post with. Should sound casual and authentic, not like a product description.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string returned by suggest_outfit.
- `new_item` (dict): The listing dictionary for the thrifted piece, used to pull in
  price, platform, and title for the caption.

**What it returns:**
<!-- Describe the return value -->
A string of 1–3 sentences written in a casual first-person voice. Mentions the
thrifted item, where it was found, the price, and how it fits into the outfit. Should sound different for different inputs.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If outfit is an empty string or new_item is missing required fields, the agent returns a fallback: "couldn't generate a fit card — outfit data was incomplete."

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The planning loop runs sequentially with conditional checks after each tool call:

1. Call search_listings(description, size, max_price).
   - If results is empty → set error message, return early. Do not proceed.
   - If results is not empty → set session["selected_item"] = results[0]. Proceed to step 2.

2. Call suggest_outfit(new_item=session["selected_item"], wardrobe=session["wardrobe"]).
   - If wardrobe["items"] is empty → return wardrobe-empty message. Do not proceed to fit card.
   - If LLM call fails → return fallback message with item title. Do not proceed.
   - If suggestion returned → set session["outfit_suggestion"] = suggestion. Proceed to step 3.

3. Call create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"]).
   - If fit card generated → set session["fit_card"] = fit_card. Return full result to user.
   - If fit card fails → return fallback message.

The loop never skips steps or calls tools out of order. It stops as soon as any step returns an error.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent maintains a session dictionary that persists across all tool calls within one
interaction. It stores:

- `session["query"]` — the original user query string
- `session["selected_item"]` — the listing dict chosen from search_listings results
- `session["wardrobe"]` — the user's wardrobe dict (passed in at the start)
- `session["outfit_suggestion"]` — the string returned by suggest_outfit
- `session["fit_card"]` — the string returned by create_fit_card
- `session["error"]` — set if any tool fails; causes the loop to return early

Each tool reads from and writes to this session dict rather than passing values directly between functions. This makes it easy to inspect state at any point and add new tools later.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | "I couldn't find any listings matching your search. Try broadening your description, adjusting your size, or raising your price limit." Pipeline stops. |
| suggest_outfit | Wardrobe is empty | "Your wardrobe is empty, I can't suggest a full outfit yet, but this piece would work well as a starting point. Add some basics to get outfit suggestions." Pipeline stops after this message. |
| create_fit_card | Outfit input is missing or incomplete | "couldn't generate a fit card, outfit data was incomplete." Returns whatever was generated up to that point. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
User query (description, size, max_price, wardrobe)

│

▼

Planning Loop

│

├─► search_listings(description, size, max_price)

│       │

│       ├── results=[] ──► "No listings found. Try adjusting your search." → STOP

│       │

│       └── results=[item, ...]

│               │

│               ▼

│         session["selected_item"] = results[0]

│               │

├─► suggest_outfit(selected_item, wardrobe)

│       │

│       ├── wardrobe empty ──► "Wardrobe is empty..." → STOP

│       ├── LLM fails ──► "Couldn't generate suggestions..." → STOP

│       │

│       └── suggestion returned

│               │

│               ▼

│         session["outfit_suggestion"] = suggestion

│               │

└─► create_fit_card(outfit_suggestion, selected_item)

│

├── fails ──► "couldn't generate fit card" → return partial result

│

└── fit_card returned

│

▼

session["fit_card"] = fit_card

│

▼

Return to user:

selected_item + outfit_suggestion + fit_card

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I'll give Claude the Tool 1 spec (inputs, return value, failure mode) and the listings data structure from this planning.md and ask it to implement search_listings() using load_listings() from data_loader.py. I'll verify by running 3 test queries, one that should match, one that should return empty, one edge case, (price exactly at limit). Same approach for suggest_outfit: I'll give Claude the Tool 2 spec plus the wardrobe schema and ask it to implement suggest_outfit() using the Groq API. I'll test with get_example_wardrobe() and get_empty_wardrobe(). For create_fit_card I'll give Claude Tool 3 spec and ask for a Groq prompt that sounds casual and varies output — I'll run it 3 times on the same input and verify the output differs each time.

**Milestone 4 — Planning loop and state management:**
I'll give Claude the Planning Loop section, State Management section, and Architecture diagram from this planning.md and ask it to implement the main agent() function that orchestrates all three tools using the session dict pattern described. I'll verify by running the complete example interaction below and checking that early termination works correctly when search_listings returns empty.

---

## A Complete Interaction (Step by Step)

     Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

FitFindr takes a natural language request from a user and breaks it into three sequential tool calls. First, search_listings() filters the mock dataset by description, size, and price to find matching items — if nothing matches, the agent stops and tells the user what to adjust. If a match is found, suggest_outfit() takes the top result and the user's wardrobe and generates outfit combinations using the style_tags and colors of both. Finally, create_fit_card() turns the best outfit suggestion into a short shareable caption. Each tool only runs if the previous one returned a valid result.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
search_listings(description="vintage graphic tee", size="M", max_price=30.0) is called. The function scans listings.json and finds lst_006 (Graphic Tee — 2003 Tour Bootleg Style, $24, size L) and lst_033 (Vintage Band Tee — Faded Grey, $19, size L) as matches based on style_tags ["graphic tee", "vintage"] and price under $30. session["selected_item"] is set to lst_006 (top result).

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
suggest_outfit(new_item=lst_006, wardrobe=get_example_wardrobe()) is called. The LLM receives the item details (black boxy graphic tee, grunge/streetwear tags) and the wardrobe (baggy dark wash jeans w_001, chunky white sneakers w_007, black denim jacket w_006). It returns: "Pair this boxy graphic tee with your baggy dark wash jeans and chunky white sneakers for an easy streetwear look. Throw the black denim jacket on top if it gets cold, the cropped cut balances the oversized teenicely." session["outfit_suggestion"] is set to this string.

**Step 3:**
<!-- Continue until the full interaction is complete -->
create_fit_card(outfit=session["outfit_suggestion"] new_item=lst_006) is called. The LLM generates a casual caption using the item price ($24), platform (depop), and outfit details. Returns: "snagged this faded bootleg tee on depop for $24 and it was made for my baggy jeans era 🖤 the oversized fit is everything" session["fit_card"] is set to this string.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The agent returns all three pieces together:
- **Found:** Graphic Tee — 2003 Tour Bootleg Style, $24, Depop (good condition)
- **Outfit suggestion:** "Pair this boxy graphic tee with your baggy dark wash jeans
  and chunky white sneakers..."
- **Fit card:** "snagged this faded bootleg tee on depop for $24 and it was made for
  my baggy jeans era 🖤"
