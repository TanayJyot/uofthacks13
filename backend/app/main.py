import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from .gemini_client import suggest_subreddits
    from .pipeline import run_product_pipeline
except ImportError:  # Allows running as a script without package context.
    from gemini_client import suggest_subreddits
    from pipeline import run_product_pipeline

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
    if not product:
        return jsonify(error="product is required"), 400

    max_subreddits = payload.get("max_subreddits", 5)
    posts_per_subreddit = payload.get("posts_per_subreddit", 10)
    comments_per_post = payload.get("comments_per_post", 10)
    archetype_count = payload.get("archetype_count", 4)
    model_name = payload.get("model")

    try:
        max_subreddits = int(max_subreddits)
        posts_per_subreddit = int(posts_per_subreddit)
        comments_per_post = int(comments_per_post)
        archetype_count = int(archetype_count)
    except (TypeError, ValueError):
        return jsonify(error="numeric fields must be integers"), 400

    try:
        result = run_product_pipeline(
            product,
            max_subreddits=max_subreddits,
            posts_per_subreddit=posts_per_subreddit,
            comments_per_post=comments_per_post,
            archetype_count=archetype_count,
            model_name=model_name,
        )
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        app.logger.error("Pipeline error: %s", exc)
        app.logger.error(traceback.format_exc())
        return jsonify(error="failed to run pipeline", details=str(exc)), 500

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
