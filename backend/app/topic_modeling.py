from typing import Dict, List


def _extract_comment_texts(archetype: Dict[str, object]) -> List[str]:
    comments = archetype.get("comments", []) or []
    texts = []
    for comment in comments:
        body = (comment.get("body") or "").strip()
        if body:
            texts.append(body)
    return texts


def add_archetype_topics(
    archetypes: List[Dict[str, object]],
    top_n: int = 5,
    product_name: str = "",
    model_name: str = None,
) -> List[Dict[str, object]]:
    try:
        from bertopic import BERTopic
        from sklearn.feature_extraction.text import CountVectorizer
    except ImportError as exc:
        raise RuntimeError("bertopic is not installed. Run `pip install bertopic`.") from exc

    for archetype in archetypes:
        documents = _extract_comment_texts(archetype)
        if len(documents) < 2:
            archetype["topics"] = []
            archetype["topic_comment_count"] = len(documents)
            continue

        vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2)
        topic_model = BERTopic(
            vectorizer_model=vectorizer,
            min_topic_size=5,
            calculate_probabilities=False,
        )
        topics, _ = topic_model.fit_transform(documents)
        topic_info = topic_model.get_topic_info()
        enriched_topics = []

        for _, row in topic_info.iterrows():
            topic_id = int(row["Topic"])
            if topic_id == -1:
                continue
            keywords = [word for word, _ in (topic_model.get_topic(topic_id) or [])][:6]
            enriched_topics.append(
                {
                    "topic_id": topic_id,
                    "count": int(row["Count"]),
                    "keywords": keywords,
                }
            )

        try:
            from .gemini_client import summarize_topics_with_gemini
        except ImportError:
            from gemini_client import summarize_topics_with_gemini

        summarized = summarize_topics_with_gemini(
            product_name,
            archetype.get("name", ""),
            enriched_topics[:top_n],
            model_name=model_name,
        )
        archetype["topics"] = summarized
        archetype["topic_comment_count"] = len(documents)

    return archetypes
