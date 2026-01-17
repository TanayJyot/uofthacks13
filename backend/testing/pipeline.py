import sys
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    from backend.app.pipeline import run_product_pipeline

    result = run_product_pipeline("iphone", max_subreddits=10, posts_per_subreddit=10)
    print("subreddits", result["subreddits"])
    print("posts", len(result["posts"]))
    print("archetypes", len(result["archetypes"]))
    if result["archetypes"]:
        print("first_archetype", result["archetypes"][0].get("name"))


if __name__ == "__main__":
    main()
