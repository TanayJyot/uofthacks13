import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import google.generativeai as genai


def _normalize_subreddit(name: str) -> str:
    cleaned = name.strip()
    cleaned = re.sub(r"^r/", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", cleaned)
    if not cleaned:
        return ""
    return f"r/{cleaned}"


def _extract_json_array(text: str) -> List[str]:
    if not text:
        return []
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass

    return re.findall(r"r/[A-Za-z0-9_]+", text)


def _extract_json_list(text: str) -> List[dict]:
    if not text:
        return []
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
        except json.JSONDecodeError:
            pass

    return []


def _load_env_fallback() -> None:
    candidate_paths = [
        Path.cwd() / ".env",
        Path.cwd() / "backend" / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]
    for env_path in candidate_paths:
        if env_path.exists():
            _load_env_file(env_path)
            break


def _load_env_file(path: Path) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip(",").strip('"').strip("'")
        if key and value:
            os.environ.setdefault(key, value)


def _get_default_model_name() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def suggest_subreddits(product_name: str, max_results: int = 10, model_name: str = None) -> List[str]:
    if not os.environ.get("GEMINI_API_KEY"):
        _load_env_fallback()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model_name = model_name or _get_default_model_name()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    prompt = (
        "You are helping pick relevant subreddit names for a product. "
        "Return only a JSON array of subreddit names as strings, each formatted like 'r/name'. "
        "Include official brand, competitor, and industry subreddits when relevant. "
        "Do not include extra commentary. "
        f"Product: {product_name}. "
        f"Return {max_results} items."
    )

    response = model.generate_content(prompt)
    raw_text = response.text or ""
    candidates = _extract_json_array(raw_text)

    normalized = []
    seen = set()
    for item in candidates:
        normalized_item = _normalize_subreddit(item)
        if normalized_item and normalized_item not in seen:
            normalized.append(normalized_item)
            seen.add(normalized_item)
        if len(normalized) >= max_results:
            break

    return normalized


def classify_user_archetypes(
    product_name: str,
    comments: Sequence[Dict[str, Optional[str]]],
    archetype_count: int = 4,
    model_name: str = None,
) -> List[Dict[str, object]]:
    if not os.environ.get("GEMINI_API_KEY"):
        _load_env_fallback()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    if archetype_count < 1:
        raise ValueError("archetype_count must be >= 1")

    model_name = model_name or _get_default_model_name()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    comment_index = {}
    serialized_comments = []
    for comment in comments:
        comment_id = comment.get("comment_id")
        body = (comment.get("body") or "").strip()
        if not comment_id or not body:
            continue
        comment_index[str(comment_id)] = comment
        trimmed_body = body[:500]
        serialized_comments.append(f"{comment_id}: {trimmed_body}")

    prompt = (
        "You are clustering Reddit comments about a product into user archetypes. "
        f"Return ONLY a JSON array with {archetype_count} objects. "
        "Each object must have keys: name, emoji, description, comment_ids. "
        "emoji must be a single emoji character suitable for UI display. "
        "comment_ids must be an array of IDs chosen ONLY from the provided list. "
        "Do not paraphrase comments. Do not include any commentary or extra keys. "
        f"Product: {product_name}. "
        "Comments:\n"
        + "\n".join(serialized_comments)
    )

    response = model.generate_content(prompt)
    raw_text = response.text or ""
    parsed = _extract_json_list(raw_text)

    archetypes = []
    for item in parsed:
        name = str(item.get("name", "")).strip()
        emoji = str(item.get("emoji", "")).strip()
        description = str(item.get("description", "")).strip()
        comment_ids = item.get("comment_ids", [])
        if not isinstance(comment_ids, list):
            comment_ids = []

        selected_comments = []
        for comment_id in comment_ids:
            comment_key = str(comment_id)
            if comment_key in comment_index:
                selected_comments.append(comment_index[comment_key])

        archetypes.append(
            {
                "name": name,
                "emoji": emoji or "👤",
                "description": description,
                "comments": selected_comments,
            }
        )

    return archetypes
