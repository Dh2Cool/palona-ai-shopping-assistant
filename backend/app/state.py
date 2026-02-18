"""Server-side session state manager."""

from typing import Any

# session_id -> {messages: [...], products: [...]}
_sessions: dict[str, dict[str, Any]] = {}
MAX_MESSAGES = 20  # Last N messages to keep
MAX_PRODUCTS = 10  # Last retrieved products to keep


def get_session(session_id: str | None) -> dict[str, Any] | None:
    """Get session state by id. Returns None if not found or id is empty."""
    if not session_id or not session_id.strip():
        return None
    return _sessions.get(session_id.strip())


def get_or_create_session(session_id: str | None) -> tuple[str, dict[str, Any]]:
    """
    Get existing session or create new one.
    Returns (session_id, state). If session_id is empty, generates a new id.
    """
    import uuid

    if not session_id or not session_id.strip():
        sid = str(uuid.uuid4())
        _sessions[sid] = {"messages": [], "products": []}
        return sid, _sessions[sid]

    sid = session_id.strip()
    if sid not in _sessions:
        _sessions[sid] = {"messages": [], "products": []}
    return sid, _sessions[sid]


def update_session(
    session_id: str,
    *,
    user_message: str | None = None,
    assistant_message: str | None = None,
    products: list[dict[str, Any]] | None = None,
) -> None:
    """Update session with new messages and/or products."""
    if not session_id or session_id not in _sessions:
        return

    s = _sessions[session_id]
    if user_message is not None:
        s["messages"] = s.get("messages", []) + [{"role": "user", "content": user_message}]
    if assistant_message is not None:
        s["messages"] = s.get("messages", []) + [
            {"role": "assistant", "content": assistant_message}
        ]
    s["messages"] = s["messages"][-MAX_MESSAGES:]

    if products is not None:
        s["products"] = products[:MAX_PRODUCTS]


def clear_session(session_id: str | None) -> None:
    """Clear session state (e.g. on New Chat)."""
    if session_id and session_id in _sessions:
        _sessions[session_id] = {"messages": [], "products": []}
