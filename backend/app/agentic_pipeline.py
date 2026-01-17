from .pipeline import get_candidate_subreddits, run_product_pipeline


def run_subreddit_discovery(product: str, max_results: int = 10, model_name: str = "gemini-1.5-flash"):
    return get_candidate_subreddits(product, max_results=max_results, model_name=model_name)


def run_product_archetype_pipeline(
    product: str,
    max_subreddits: int = 5,
    posts_per_subreddit: int = 10,
    comments_per_post: int = 10,
    archetype_count: int = 4,
    model_name: str = "gemini-1.5-flash",
):
    return run_product_pipeline(
        product,
        max_subreddits=max_subreddits,
        posts_per_subreddit=posts_per_subreddit,
        comments_per_post=comments_per_post,
        archetype_count=archetype_count,
        model_name=model_name,
    )
