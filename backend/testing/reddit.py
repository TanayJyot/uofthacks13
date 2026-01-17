import os
from pathlib import Path
import importlib.util


def load_env(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip(",").strip('"').strip("'")
        if key and value:
            os.environ.setdefault(key, value)


def load_reddit_module():
    module_path = Path(__file__).resolve().parents[1] / "app" / "reddit_praw.py"
    spec = importlib.util.spec_from_file_location("reddit_praw", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    load_env("backend/.env")
    reddit_praw = load_reddit_module()

    posts = reddit_praw.get_subreddit_hot_posts("python", k=10)
    print("posts", len(posts))
    if not posts:
        return
    print("first_post_keys", sorted(posts[0].keys()))
    print("top_comments_count", len(posts[0]["top_comments"]))
    if posts[0]["top_comments"]:
        print("first_comment_keys", sorted(posts[0]["top_comments"][0].keys()))
    print(posts)
    print(len(posts))


if __name__ == "__main__":
    main()
