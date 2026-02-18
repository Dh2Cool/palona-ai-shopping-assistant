"""Single agent orchestration: intent routing and response generation."""

from typing import Any

from .llm import chat_completion, describe_image
from .retrieval import search_products

# --- Intents (strict, spec-aligned) ---
INTENT_SEARCH = "SEARCH"
INTENT_CHAT = "CHAT"
INTENT_IMAGE_SEARCH = "IMAGE_SEARCH"

SYSTEM_PROMPT = """You are Palona, a friendly AI shopping assistant like Amazon Rufus.
You can:
1. Have general conversations - introduce yourself, answer questions about your capabilities
2. Answer product-specific questions - reviews, ratings, specs, features, comparisons (e.g., "how are its reviews?", "what are the specs?")
3. Recommend products based on text descriptions (e.g., "recommend a t-shirt for sports")
4. Find products based on images users upload

When the user asks about a specific product (reviews, ratings, specs, how it works), use the product data provided to answer directly.
When recommending, mention names, key features, prices, and ratings.
Be conversational and helpful. Keep responses concise (2-5 sentences) unless the user asks for more.
If no products match, suggest different keywords."""

INTENT_DETECTION_PROMPT = """Classify the user's intent. Reply with EXACTLY one word from this list:
- CHAT: greetings, questions about you, what you can do, small talk, general conversation
- SEARCH: product questions (reviews, ratings, specs, compare), product suggestions (recommend, suggest, find me, looking for, need a, want to buy)

Reply with only: CHAT or SEARCH. No other text."""


async def detect_intent(message: str, has_image: bool) -> str:
    """Detect user intent. Returns one of SEARCH, CHAT, IMAGE_SEARCH."""
    if has_image:
        return INTENT_IMAGE_SEARCH

    messages = [
        {"role": "system", "content": INTENT_DETECTION_PROMPT},
        {"role": "user", "content": message or "hello"},
    ]
    result = await chat_completion(messages, temperature=0)
    result = result.upper().strip()
    if "SEARCH" in result:
        return INTENT_SEARCH
    return INTENT_CHAT


def _is_follow_up(message: str, previous_products: list) -> bool:
    """Check if message explicitly references previous products (e.g. 'the first one', 'compare them')."""
    if not previous_products:
        return False
    msg = message.lower().strip()
    follow_up_phrases = [
        "first one", "second one", "third one", "that one", "this one",
        "the first", "the second", "compare them", "tell me more", "more about",
        "what about that", "how about that", "between them", "which one", "the difference",
        "compare the", "tell me about the first", "tell me about the second",
    ]
    return any(p in msg for p in follow_up_phrases)


async def process_message(
    message: str,
    image_base64: str | None,
    catalog: list[dict[str, Any]],
    history: list[dict[str, str]] | None = None,
    previous_products: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Process user message (and optional image) through the unified agent.
    Uses chat history for conversational context.
    Returns {response, products, intent}.
    """
    history = history or []
    previous_products = previous_products or []
    history = history[-20:] if len(history) > 20 else history

    has_image = bool(image_base64 and image_base64.strip())

    search_query = message or ""
    if has_image:
        search_query = await describe_image(image_base64)
        intent = INTENT_IMAGE_SEARCH
    else:
        intent = await detect_intent(message, False)

    # Route by intent
    if intent == INTENT_CHAT:
        llm_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *[{"role": h["role"], "content": h["content"]} for h in history],
            {"role": "user", "content": message or "Hello!"},
        ]
        response = await chat_completion(llm_messages)
        return {"response": response, "products": [], "intent": intent}

    # SEARCH or IMAGE_SEARCH: use ChromaDB retrieval
    query = search_query if search_query else message
    use_previous = not has_image and _is_follow_up(message, previous_products)
    if use_previous:
        products = previous_products[:5]
    else:
        search_query_used = query
        if "," in query and any(
            w in query.lower() for w in ("how", "what", "reviews", "ratings", "specs", "compare")
        ):
            before_comma = query.split(",")[0].strip()
            if len(before_comma) > 10:
                search_query_used = before_comma
        products = search_products(search_query_used, catalog, top_k=5)

    def _product_context(p: dict[str, Any]) -> str:
        parts = [f"Name: {p.get('name', '')}", f"Price: {p.get('price', '')}"]
        if p.get("rating") is not None:
            parts.append(f"Rating: {p['rating']}/5 stars")
        rc = p.get("review_count")
        if rc is not None and isinstance(rc, int):
            parts.append(f"Review count: {rc:,}")
        desc = (p.get("description") or "")[:200]
        if desc:
            parts.append(f"Description: {desc}...")
        specs = (p.get("specs_text") or "")[:300]
        if specs:
            parts.append(f"Specs: {specs}...")
        reviews = p.get("reviews_json") or ""
        if reviews:
            parts.append(f"Review snippets: {reviews[:500]}...")
        return "\n  ".join(parts)

    if not products:
        if has_image:
            current_turn = f"""The user uploaded an image. We analyzed it and described it as: "{search_query}"

We found no products in our catalog that match this description.

Write a helpful 1-2 sentence response. Say we searched based on the image but don't have matching products. Suggest they try describing what they're looking for in words, or try different keywords. Do NOT say you cannot view images - we already processed the image."""
        else:
            current_turn = f"""The user asked: "{message}"
We found no products that closely match this query in our catalog.

Write a helpful 1-2 sentence response. Politely explain we don't have good matches and suggest they try different keywords or browse our general selection."""
    else:
        product_blocks = "\n\n".join(
            f"Product {i+1}:\n  " + _product_context(p) for i, p in enumerate(products)
        )
        if has_image:
            intro = f"""The user uploaded an image. We analyzed it and described it as: "{search_query}"

Matching products from our catalog:"""
        else:
            intro = f"""The user asked: "{message}"

Matching products from our catalog:"""
        current_turn = f"""{intro}

{product_blocks}

Instructions:
- Recommend ONLY the products listed above. Do NOT mention products not in the list.
- If the user uploaded an image, we already processed it - describe the matches based on the image analysis. Do NOT say you cannot view images.
- If the user asked about reviews/ratings, use the rating and review count.
- If the user asked about specs or features, use the description and specs data.
- If the user asked to COMPARE multiple products (e.g. "compare them", "which one is better"), format your response as a Markdown table with columns: Product | Price | Rating | Key difference. Then add 1-2 sentences summarizing your recommendation.
- Be conversational like Amazon Rufus. Answer the specific question they asked, then offer to help with more."""

    llm_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *[{"role": h["role"], "content": h["content"]} for h in history],
        {"role": "user", "content": current_turn},
    ]
    response = await chat_completion(llm_messages)

    return {
        "response": response,
        "products": products,
        "intent": intent,
    }
