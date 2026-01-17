try:
    from .gemini_client import classify_user_archetypes, suggest_subreddits
    from .reddit_praw import get_subreddit_hot_posts
    from .topic_modeling import add_archetype_topics
except ImportError:  # Allows running as a script without package context.
    from gemini_client import classify_user_archetypes, suggest_subreddits
    from reddit_praw import get_subreddit_hot_posts
    from topic_modeling import add_archetype_topics


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
):
    subreddits = suggest_subreddits(product, max_results=max_subreddits, model_name=model_name)
    all_posts = []
    all_comments = []

    for subreddit in subreddits:
        subreddit_name = subreddit.replace("r/", "")
        posts = get_subreddit_hot_posts(subreddit_name, k=posts_per_subreddit)
        for post in posts:
            all_posts.append(post)
            top_comments = post.get("top_comments", [])[:comments_per_post]
            for comment in top_comments:
                if comment.get("body"):
                    all_comments.append(comment)

    archetypes = classify_user_archetypes(
        product,
        all_comments,
        archetype_count=archetype_count,
        model_name=model_name,
    )
    archetypes = add_archetype_topics(archetypes)

    return {
        "product": product,
        "subreddits": subreddits,
        "posts": all_posts,
        "archetypes": archetypes,
    }
