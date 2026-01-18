import os
from pathlib import Path
from typing import Dict, List, Optional

import praw


def _get_reddit_client() -> praw.Reddit:
    if not os.environ.get("REDDIT_CLIENT_ID") or not os.environ.get("REDDIT_CLIENT_SECRET"):
        _load_env_fallback()

    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "uofthacks13 v1.0")

    if not client_id or not client_secret:
        raise RuntimeError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set")

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


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


def _extract_top_comments(submission: praw.models.Submission, limit: int = 10) -> List[Dict[str, Optional[str]]]:
    submission.comments.replace_more(limit=0)
    top_comments = []
    for comment in submission.comments.list()[:limit]:
        body = (comment.body or "").strip()
        if body.lower() in {"[removed]", "[deleted]"}:
            continue
        top_comments.append(
            {
                "comment_id": comment.id,
                "body": body,
                "author": str(comment.author) if comment.author else None,
                "created_utc": comment.created_utc,
                "score": comment.score,
                "parent_id": comment.parent_id,
                "permalink": f"https://www.reddit.com{comment.permalink}",
                "post_title": submission.title,
                "subreddit": str(submission.subreddit),
            }
        )
    return top_comments


def get_subreddit_posts(subreddit_name: str, k: int = 10, type: str = "hot") -> List[Dict[str, Optional[str]]]:
    reddit = _get_reddit_client()
    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    if type == "hot":
        for submission in subreddit.hot(limit=k):
            posts.append(
                {
                    "post_id": submission.id,
                    "title": submission.title,
                    "body": submission.selftext,
                    "author": str(submission.author) if submission.author else None,
                    "created_utc": submission.created_utc,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "url": submission.url,
                    "permalink": f"https://www.reddit.com{submission.permalink}",
                    "subreddit": str(submission.subreddit),
                    "top_comments": _extract_top_comments(submission, limit=10),
                }
            )
    elif type == "new":
        for submission in subreddit.new(limit=k):
            posts.append(
                {
                    "post_id": submission.id,
                    "title": submission.title,
                    "body": submission.selftext,
                    "author": str(submission.author) if submission.author else None,
                    "created_utc": submission.created_utc,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "url": submission.url,
                    "permalink": f"https://www.reddit.com{submission.permalink}",
                    "subreddit": str(submission.subreddit),
                    "top_comments": _extract_top_comments(submission, limit=10),
                }
            )

    return posts


def get_subreddit_hot_posts(subreddit_name: str, k: int = 10) -> List[Dict[str, Optional[str]]]:
    return get_subreddit_posts(subreddit_name, k=k, type="hot")


def get_subreddit_metadata(subreddit_name: str) -> Dict[str, Optional[str]]:
    reddit = _get_reddit_client()
    subreddit = reddit.subreddit(subreddit_name)
    return {
        "name": f"r/{subreddit.display_name}",
        "title": subreddit.title,
        "description": subreddit.public_description or "",
        "subscribers": subreddit.subscribers,
        "url": subreddit.url,
    }
