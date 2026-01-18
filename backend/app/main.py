import traceback
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from .gemini_client import (
        classify_comments_into_archetypes,
        score_archetype_satisfaction_acsi,
        suggest_subreddits,
    )
    from .pipeline import run_product_pipeline
    from .storage import (
        add_product,
        find_product_by_name,
        get_product,
        list_products,
        update_product,
        update_product_state,
    )
    from .topic_modeling import add_archetype_topics
except ImportError:  # Allows running as a script without package context.
    from gemini_client import (
        classify_comments_into_archetypes,
        score_archetype_satisfaction_acsi,
        suggest_subreddits,
    )
    from pipeline import run_product_pipeline
    from storage import (
        add_product,
        find_product_by_name,
        get_product,
        list_products,
        update_product,
        update_product_state,
    )
    from topic_modeling import add_archetype_topics

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify(status="ok")


@app.route("/api/subreddits", methods=["POST"])
def subreddits():
    payload = request.get_json(silent=True) or {}
    product = (payload.get("product") or "").strip()
    if not product:
        return jsonify(error="product is required"), 400

    max_results = payload.get("max_results", 10)
    model_name = payload.get("model")

    try:
        max_results = int(max_results)
    except (TypeError, ValueError):
        return jsonify(error="max_results must be an integer"), 400

    if max_results < 1:
        return jsonify(error="max_results must be >= 1"), 400

    try:
        subreddits_list = suggest_subreddits(product, max_results=max_results, model_name=model_name)
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        return jsonify(error="failed to fetch subreddits", details=str(exc)), 500

    return jsonify(product=product, subreddits=subreddits_list)


@app.route("/api/pipeline", methods=["POST"])
def pipeline():
    payload = request.get_json(silent=True) or {}
    product = (payload.get("product") or "").strip()
    product_id = (payload.get("product_id") or "").strip()
    if not product:
        if not product_id:
            return jsonify(error="product is required"), 400

    max_subreddits = payload.get("max_subreddits", 5)
    posts_per_subreddit = payload.get("posts_per_subreddit", 10)
    comments_per_post = payload.get("comments_per_post", 10)
    archetype_count = payload.get("archetype_count", 4)
    min_comment_length = payload.get("min_comment_length", 30)
    request_delay = payload.get("request_delay", 1.0)
    model_name = payload.get("model")

    try:
        max_subreddits = int(max_subreddits)
        posts_per_subreddit = int(posts_per_subreddit)
        comments_per_post = int(comments_per_post)
        archetype_count = int(archetype_count)
        min_comment_length = int(min_comment_length)
        request_delay = float(request_delay)
    except (TypeError, ValueError):
        return jsonify(error="numeric fields must be integers"), 400

    try:
        if product_id:
            product_record = get_product(product_id)
            if not product_record:
                return jsonify(error="product not found"), 404
            product = product_record.get("name", product)
        else:
            existing = find_product_by_name(product)
            product_record = existing or add_product(product)
            product_id = product_record["product_id"]

        result = run_product_pipeline(
            product,
            max_subreddits=max_subreddits,
            posts_per_subreddit=posts_per_subreddit,
            comments_per_post=comments_per_post,
            archetype_count=archetype_count,
            model_name=model_name,
            min_comment_length=min_comment_length,
            request_delay=request_delay,
        )
        satisfaction_archetypes = score_archetype_satisfaction_acsi(
            product,
            result.get("archetypes", []),
            model_name=model_name,
        )
        overall_score = 0
        if satisfaction_archetypes:
            overall_score = sum(
                item.get("overall_score", 0) for item in satisfaction_archetypes
            ) / len(satisfaction_archetypes)
        satisfaction = {
            "model": {
                "name": "ACSI",
                "citation": "The American Customer Satisfaction Index: Nature, Purpose, and Findings (1996).",
                "link": "https://doi.org/10.2307/1251898",
            },
            "overall_score": round(overall_score, 2),
            "archetypes": satisfaction_archetypes,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        update_product(
            product_id,
            {
                "subreddits": result.get("subreddits", []),
                "posts": result.get("posts", []),
                "archetypes": result.get("archetypes", []),
                "topics_ready": False,
                "satisfaction": satisfaction,
                "satisfaction_history": [
                    *product_record.get("satisfaction_history", []),
                    {
                        "created_at": satisfaction["updated_at"],
                        "overall_score": satisfaction["overall_score"],
                        "archetypes": [
                            {
                                "name": item.get("name"),
                                "overall_score": item.get("overall_score", 0),
                            }
                            for item in satisfaction_archetypes
                        ],
                    },
                ],
            },
        )
        stored = {
            "product_id": product_id,
            "product_name": product_record.get("name"),
            **result,
            "topics_ready": False,
            "satisfaction": satisfaction,
            "satisfaction_history": product_record.get("satisfaction_history", [])
            + [
                {
                    "created_at": satisfaction["updated_at"],
                    "overall_score": satisfaction["overall_score"],
                    "archetypes": [
                        {
                            "name": item.get("name"),
                            "overall_score": item.get("overall_score", 0),
                        }
                        for item in satisfaction_archetypes
                    ],
                }
            ],
        }
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        app.logger.error("Pipeline error: %s", exc)
        app.logger.error(traceback.format_exc())
        return jsonify(error="failed to run pipeline", details=str(exc)), 500

    return jsonify(stored)


@app.route("/api/products", methods=["GET"])
def products():
    return jsonify(list_products())


@app.route("/api/products", methods=["POST"])
def create_product():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify(error="name is required"), 400
    existing = find_product_by_name(name)
    if existing:
        return jsonify(existing)
    return jsonify(add_product(name))


@app.route("/api/products/<product_id>", methods=["GET"])
def product_detail(product_id: str):
    product = get_product(product_id)
    if not product:
        return jsonify(error="product not found"), 404
    if isinstance(product.get("satisfaction"), dict):
        product["satisfaction"]["model"] = {
            **product["satisfaction"].get("model", {}),
            "citation": "The American Customer Satisfaction Index: Nature, Purpose, and Findings (1996).",
        }
    return jsonify(product)


@app.route("/api/topics", methods=["POST"])
def topics():
    payload = request.get_json(silent=True) or {}
    product_id = (payload.get("product_id") or "").strip()
    top_n = payload.get("top_n", 5)

    if not product_id:
        return jsonify(error="product_id is required"), 400

    try:
        top_n = int(top_n)
    except (TypeError, ValueError):
        return jsonify(error="top_n must be an integer"), 400

    product = get_product(product_id)
    if not product:
        return jsonify(error="product not found"), 404

    try:
        archetypes = product.get("archetypes", [])
        updated_archetypes = add_archetype_topics(archetypes, top_n=top_n)
        updated = update_product_state(
            product_id,
            {"archetypes": updated_archetypes, "topics_ready": True},
        )
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        app.logger.error("Topic modeling error: %s", exc)
        app.logger.error(traceback.format_exc())
        return jsonify(error="failed to run topic modeling", details=str(exc)), 500

    return jsonify(updated)


@app.route("/api/refresh", methods=["POST"])
def refresh():
    payload = request.get_json(silent=True) or {}
    product_id = (payload.get("product_id") or "").strip()
    max_posts = payload.get("max_posts", 10)
    request_delay = payload.get("request_delay", 1.0)
    model_name = payload.get("model")

    if not product_id:
        return jsonify(error="product_id is required"), 400

    try:
        max_posts = int(max_posts)
        request_delay = float(request_delay)
    except (TypeError, ValueError):
        return jsonify(error="max_posts must be an integer"), 400

    product = get_product(product_id)
    if not product:
        return jsonify(error="product not found"), 404

    subreddits = product.get("subreddits", [])
    if not subreddits:
        return jsonify(error="no subreddits saved for product"), 400

    try:
        from .reddit_praw import get_subreddit_posts
    except ImportError:
        from reddit_praw import get_subreddit_posts

    new_comments = []
    min_comment_length = payload.get("min_comment_length", 30)
    try:
        min_comment_length = int(min_comment_length)
    except (TypeError, ValueError):
        return jsonify(error="min_comment_length must be an integer"), 400

    for subreddit in subreddits:
        if request_delay:
            import time
            time.sleep(request_delay)
        subreddit_name = subreddit.replace("r/", "")
        try:
            posts = get_subreddit_posts(subreddit_name, k=max_posts, type="new")
        except Exception as exc:
            app.logger.warning("Refresh failed for %s: %s", subreddit_name, exc)
            continue
        for post in posts:
            for comment in post.get("top_comments", []):
                body = (comment.get("body") or "").strip()
                if (
                    body
                    and body.lower() not in {"[removed]", "[deleted]"}
                    and len(body) >= min_comment_length
                ):
                    new_comments.append(
                        {
                            **comment,
                            "body": body,
                            "post_title": post.get("title"),
                            "subreddit": post.get("subreddit"),
                        }
                    )

    existing_comment_ids = set()
    for archetype in product.get("archetypes", []):
        for comment in archetype.get("comments", []) or []:
            if comment.get("comment_id"):
                existing_comment_ids.add(str(comment["comment_id"]))

    new_comments = [
        comment
        for comment in new_comments
        if str(comment.get("comment_id")) not in existing_comment_ids
    ]

    if not new_comments:
        return jsonify({**product, "new_comments_added": 0})

    try:
        grouped = classify_comments_into_archetypes(
            product.get("name", ""),
            product.get("archetypes", []),
            new_comments,
            model_name=model_name,
        )
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        app.logger.error("Refresh error: %s", exc)
        app.logger.error(traceback.format_exc())
        return jsonify(error="failed to refresh comments", details=str(exc)), 500

    updated_archetypes = []
    grouped_map = {item.get("name"): item.get("comments", []) for item in grouped}
    for archetype in product.get("archetypes", []):
        name = archetype.get("name")
        additional = grouped_map.get(name, [])
        if additional:
            archetype = {**archetype, "comments": archetype.get("comments", []) + additional}
        updated_archetypes.append(archetype)

    satisfaction_archetypes = score_archetype_satisfaction_acsi(
        product.get("name", ""),
        updated_archetypes,
        model_name=model_name,
    )
    overall_score = 0
    if satisfaction_archetypes:
        overall_score = sum(
            item.get("overall_score", 0) for item in satisfaction_archetypes
        ) / len(satisfaction_archetypes)
    satisfaction = {
        "model": {
            "name": "ACSI",
            "citation": "The American Customer Satisfaction Index: Nature, Purpose, and Findings (1996).",
            "link": "https://doi.org/10.2307/1251898",
        },
        "overall_score": round(overall_score, 2),
        "archetypes": satisfaction_archetypes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    updated = update_product(
        product_id,
        {
            "archetypes": updated_archetypes,
            "topics_ready": False,
            "satisfaction": satisfaction,
            "satisfaction_history": [
                *product.get("satisfaction_history", []),
                {
                    "created_at": satisfaction["updated_at"],
                    "overall_score": satisfaction["overall_score"],
                    "archetypes": [
                        {
                            "name": item.get("name"),
                            "overall_score": item.get("overall_score", 0),
                        }
                        for item in satisfaction_archetypes
                    ],
                },
            ],
        },
    )
    if updated:
        updated["new_comments_added"] = len(new_comments)

    return jsonify(updated)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
