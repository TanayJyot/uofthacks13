try:
    from .gemini_client import (
        classify_user_archetypes,
        filter_subreddits_by_description,
        suggest_subreddits,
    )
    from .reddit_praw import get_subreddit_hot_posts, get_subreddit_metadata
except ImportError:  # Allows running as a script without package context.
    from gemini_client import (
        classify_user_archetypes,
        filter_subreddits_by_description,
        suggest_subreddits,
    )
    from reddit_praw import get_subreddit_hot_posts, get_subreddit_metadata


def get_candidate_subreddits(product: str, max_results: int = 10, model_name: str = None):
    return suggest_subreddits(product, max_results=max_results, model_name=model_name)


def classify_comments_to_archetypes(
    product: str,
    comments,
    archetype_count: int = 4,
    model_name: str = None,
):
    return classify_user_archetypes(
        product,
        comments,
        archetype_count=archetype_count,
        model_name=model_name,
    )


def run_product_pipeline(
    product: str,
    max_subreddits: int = 5,
    posts_per_subreddit: int = 10,
    comments_per_post: int = 10,
    archetype_count: int = 4,
    model_name: str = None,
    min_comment_length: int = 30,
    request_delay: float = 1.0,
):
    subreddits = suggest_subreddits(product, max_results=max_subreddits, model_name=model_name)
    subreddit_metadata = []
    for subreddit in subreddits:
        subreddit_name = subreddit.replace("r/", "")
        try:
            subreddit_metadata.append(get_subreddit_metadata(subreddit_name))
        except Exception:
            continue
    if subreddit_metadata:
        allowed = filter_subreddits_by_description(product, subreddit_metadata, model_name=model_name)
        subreddits = [entry for entry in subreddits if entry in allowed]
    all_posts = []
    all_comments = []

    for subreddit in subreddits:
        if request_delay:
            import time
            time.sleep(request_delay)
        subreddit_name = subreddit.replace("r/", "")
        try:
            posts = get_subreddit_hot_posts(subreddit_name, k=posts_per_subreddit)
        except Exception as exc:
            all_posts.append(
                {
                    "subreddit": subreddit,
                    "error": f"failed to fetch posts: {exc}",
                }
            )
            continue
        for post in posts:
            all_posts.append(post)
            top_comments = post.get("top_comments", [])[:comments_per_post]
            for comment in top_comments:
                body = (comment.get("body") or "").strip()
                if body and len(body) >= min_comment_length:
                    all_comments.append(
                        {
                            **comment,
                            "body": body,
                            "post_title": post.get("title"),
                            "subreddit": post.get("subreddit"),
                        }
                    )

    archetypes = classify_user_archetypes(
        product,
        all_comments,
        archetype_count=archetype_count,
        model_name=model_name,
    )

    return {
        "product": product,
        "subreddits": subreddits,
        "posts": all_posts,
        "archetypes": archetypes,
    }
