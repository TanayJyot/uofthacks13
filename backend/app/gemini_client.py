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


def classify_comments_into_archetypes(
    product_name: str,
    archetypes: Sequence[Dict[str, object]],
    comments: Sequence[Dict[str, Optional[str]]],
    model_name: str = None,
) -> List[Dict[str, object]]:
    if not os.environ.get("GEMINI_API_KEY"):
        _load_env_fallback()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

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

    archetype_descriptions = []
    for item in archetypes:
        name = item.get("name", "")
        description = item.get("description", "")
        archetype_descriptions.append(f"- {name}: {description}")

    prompt = (
        "Assign each comment to ONE of the existing archetypes below. "
        "Return ONLY a JSON array of objects with keys: name, comment_ids. "
        "The name must match one of the archetype names exactly. "
        "comment_ids must be drawn only from the provided list. "
        f"Product: {product_name}. "
        "Archetypes:\n"
        + "\n".join(archetype_descriptions)
        + "\nComments:\n"
        + "\n".join(serialized_comments)
    )

    response = model.generate_content(prompt)
    raw_text = response.text or ""
    parsed = _extract_json_list(raw_text)

    grouped = []
    for item in parsed:
        name = str(item.get("name", "")).strip()
        comment_ids = item.get("comment_ids", [])
        if not isinstance(comment_ids, list):
            comment_ids = []
        selected_comments = []
        for comment_id in comment_ids:
            comment_key = str(comment_id)
            if comment_key in comment_index:
                selected_comments.append(comment_index[comment_key])
        grouped.append({"name": name, "comments": selected_comments})

    return grouped


def score_archetype_satisfaction_acsi(
    product_name: str,
    archetypes: Sequence[Dict[str, object]],
    model_name: str = None,
    max_comments: int = 20,
) -> List[Dict[str, object]]:
    if not os.environ.get("GEMINI_API_KEY"):
        _load_env_fallback()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model_name = model_name or _get_default_model_name()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    payload_sections = []
    for archetype in archetypes:
        name = archetype.get("name", "")
        description = archetype.get("description", "")
        comments = archetype.get("comments", []) or []
        serialized_comments = []
        for comment in comments[:max_comments]:
            comment_id = comment.get("comment_id")
            body = (comment.get("body") or "").strip()
            if not comment_id or not body:
                continue
            serialized_comments.append(f"{comment_id}: {body[:500]}")
        payload_sections.append(
            f"Archetype: {name}\nDescription: {description}\nComments:\n"
            + "\n".join(serialized_comments)
        )

    prompt = (
        "You are scoring customer satisfaction using the ACSI framework. "
        "Return ONLY a JSON array with one object per archetype. "
        "Each object must have: name, overall_score, metrics. "
        "metrics must be an array of objects with keys: metric, score, reasoning, "
        "confidence, evidence_comment_ids. "
        "Scores are 0-100. confidence is 0-1. "
        "Use ONLY the provided comment_ids for evidence_comment_ids. "
        "Metrics (exact names): Expectations Match, Perceived Quality, "
        "Perceived Value, Overall Satisfaction, Loyalty / Switch Intent. "
        f"Product: {product_name}.\n"
        + "\n\n".join(payload_sections)
    )

    response = model.generate_content(prompt)
    raw_text = response.text or ""
    parsed = _extract_json_list(raw_text)

    scored = []
    for item in parsed:
        name = str(item.get("name", "")).strip()
        overall_score = item.get("overall_score", 0)
        metrics = item.get("metrics", [])
        if not isinstance(metrics, list):
            metrics = []
        cleaned_metrics = []
        for metric in metrics:
            if not isinstance(metric, dict):
                continue
            cleaned_metrics.append(
                {
                    "metric": str(metric.get("metric", "")).strip(),
                    "score": metric.get("score", 0),
                    "reasoning": str(metric.get("reasoning", "")).strip(),
                    "confidence": metric.get("confidence", 0),
                    "evidence_comment_ids": metric.get("evidence_comment_ids", []),
                }
            )
        scored.append(
            {
                "name": name,
                "overall_score": overall_score,
                "metrics": cleaned_metrics,
            }
        )

    return scored


def filter_subreddits_by_description(
    product_name: str,
    subreddits: Sequence[Dict[str, str]],
    model_name: str = None,
) -> List[str]:
    if not os.environ.get("GEMINI_API_KEY"):
        _load_env_fallback()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model_name = model_name or _get_default_model_name()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    items = []
    for entry in subreddits:
        name = entry.get("name", "")
        description = entry.get("description", "")
        items.append(f"{name}: {description[:500]}")

    prompt = (
        "You are filtering candidate subreddits for a product. "
        "Return ONLY a JSON array of objects with keys: name, relevant. "
        "relevant must be 'yes' or 'no'. Use the descriptions to decide. "
        f"Product: {product_name}. "
        "Candidates:\n"
        + "\n".join(items)
    )

    response = model.generate_content(prompt)
    raw_text = response.text or ""
    parsed = _extract_json_list(raw_text)

    allowed = []
    for item in parsed:
        name = str(item.get("name", "")).strip()
        relevant = str(item.get("relevant", "")).strip().lower()
        if name and relevant == "yes":
            allowed.append(name)

    return allowed
