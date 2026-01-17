import os
from pathlib import Path
import importlib.util

def load_env(path):
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip(",").strip('"').strip("'")
        if key and value:
            os.environ[key] = value

load_env("backend/.env")

spec = importlib.util.spec_from_file_location("reddit_praw", "backend/app/reddit_praw.py")
reddit_praw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reddit_praw)

posts = reddit_praw.get_subreddit_hot_posts("python", k=2)
print("posts", len(posts))
print("first_post_keys", sorted(posts[0].keys()))
print("top_comments_count", len(posts[0]["top_comments"]))
print("first_comment_keys", sorted(posts[0]["top_comments"][0].keys()) if posts[0]["top_comments"] else [])

