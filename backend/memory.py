# In-memory store (per-process). Replace with Redis for production.
_store: dict[str, dict] = {}


def get_memory(user_id: str) -> dict:
    return _store.setdefault(user_id, {})


def update_memory(user_id: str, data: dict) -> None:
    mem = _store.setdefault(user_id, {})

    relevant = ["date", "slot", "symptom", "doctor"]

    cleaned = {}

    for k, v in data.items():
        if k not in relevant:
            continue
        if not v:
            continue

        # 🔥 NORMALIZE SLOT (CRITICAL FIX)
        if k == "slot":
            v = str(v).strip()
            if ":" not in v and v.isdigit():
                v = f"{v}:00"

        cleaned[k] = v

    # ✅ merge (not overwrite blindly)
    mem.update(cleaned)


def clear_memory(user_id: str) -> None:
    _store[user_id] = {}


def inspect_memory(user_id: str) -> dict:
    """Debug helper."""
    return _store.get(user_id, {})