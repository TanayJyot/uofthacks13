import { useEffect, useMemo, useState } from "react";
import "./App.css";

const quickStarts = ["iPhone", "Notion", "Tesla", "AirPods Pro", "Figma"];

function App() {
  const [newProduct, setNewProduct] = useState("");
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [data, setData] = useState(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [topicsLoading, setTopicsLoading] = useState(false);
  const [refreshLoading, setRefreshLoading] = useState(false);
  const [error, setError] = useState("");
  const [commentSort, setCommentSort] = useState("recent");
  const [expandedMetric, setExpandedMetric] = useState(null);

  const stats = useMemo(() => {
    if (!data) return null;
    const commentCount = data.archetypes?.reduce((sum, item) => {
      return sum + (item.comments?.length || 0);
    }, 0);
    return {
      subreddits: data.subreddits?.length || 0,
      posts: data.posts?.length || 0,
      comments: commentCount || 0,
    };
  }, [data]);

  const loadProducts = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/products");
      const payload = await response.json();
      if (response.ok) {
        setProducts(payload);
        if (!selectedProduct && payload.length > 0) {
          setSelectedProduct(payload[0]);
        }
      }
    } catch (err) {
      setError("Failed to load products.");
    }
  };

  const loadProductDetail = async (productId) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`http://localhost:5000/api/products/${productId}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Failed to load product");
      }
      setData(payload);
      setActiveIndex(0);
    } catch (err) {
      setError(err.message || "Failed to load product");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    if (selectedProduct) {
      loadProductDetail(selectedProduct.product_id);
    }
  }, [selectedProduct]);

  const createProduct = async () => {
    if (!newProduct.trim()) {
      setError("Enter a product name.");
      return;
    }
    setError("");
    try {
      const response = await fetch("http://localhost:5000/api/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newProduct.trim() }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Failed to create product");
      }
      setNewProduct("");
      await loadProducts();
      setSelectedProduct(payload);
    } catch (err) {
      setError(err.message || "Failed to create product");
    }
  };

  const runPipeline = async (event) => {
    event.preventDefault();
    if (!selectedProduct) {
      setError("Select or create a product first.");
      return;
    }
    setLoading(true);
    setError("");
    setData(null);

    try {
      const payloadBody = { product_id: selectedProduct.product_id };

      const response = await fetch("http://localhost:5000/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payloadBody),
      });
      const payload = await response.json();
      if (!response.ok) {
        const message = payload.details
          ? `${payload.error || "Pipeline failed"}: ${payload.details}`
          : payload.error || "Pipeline failed";
        throw new Error(message);
      }

      setData(payload);
      setActiveIndex(0);
    } catch (err) {
      setError(err.message || "Pipeline failed");
    } finally {
      setLoading(false);
    }
  };

  const runTopics = async () => {
    if (!selectedProduct) {
      setError("Select a product first.");
      return;
    }
    setTopicsLoading(true);
    setError("");
    try {
      const response = await fetch("http://localhost:5000/api/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: selectedProduct.product_id }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Topic modeling failed");
      }
      setData(payload);
    } catch (err) {
      setError(err.message || "Topic modeling failed");
    } finally {
      setTopicsLoading(false);
    }
  };

  const refreshPipeline = async () => {
    if (!selectedProduct) {
      setError("Select a product first.");
      return;
    }
    setRefreshLoading(true);
    setError("");
    try {
      const response = await fetch("http://localhost:5000/api/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: selectedProduct.product_id }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Refresh failed");
      }
      setData(payload);
    } catch (err) {
      setError(err.message || "Refresh failed");
    } finally {
      setRefreshLoading(false);
    }
  };

  const archetypes = data?.archetypes || [];
  const activeArchetype = archetypes[activeIndex];
  const satisfaction = data?.satisfaction;
  const satisfactionHistory = data?.satisfaction_history || [];
  const activeMetricAverage = (() => {
    if (!satisfaction || !activeArchetype) return 0;
    const match = (satisfaction.archetypes || []).find(
      (item) => item.name === activeArchetype.name
    );
    if (!match || !Array.isArray(match.metrics) || match.metrics.length === 0) {
      return 0;
    }
    const total = match.metrics.reduce((sum, metric) => {
      return sum + (metric.score ?? 0);
    }, 0);
    return total / match.metrics.length;
  })();
  const formatTimestamp = (value) => {
    if (!value) return "Unknown time";
    const date = new Date(Number(value) * 1000);
    if (Number.isNaN(date.getTime())) return "Unknown time";
    const diffMs = date.getTime() - Date.now();
    const diffSec = Math.round(diffMs / 1000);
    const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
    const units = [
      ["year", 60 * 60 * 24 * 365],
      ["month", 60 * 60 * 24 * 30],
      ["week", 60 * 60 * 24 * 7],
      ["day", 60 * 60 * 24],
      ["hour", 60 * 60],
      ["minute", 60],
      ["second", 1],
    ];
    for (const [unit, seconds] of units) {
      if (Math.abs(diffSec) >= seconds || unit === "second") {
        return rtf.format(Math.round(diffSec / seconds), unit);
      }
    }
    return "Unknown time";
  };
  const sortedComments = [...(activeArchetype?.comments || [])].sort((a, b) => {
    if (commentSort === "score") {
      return (b.score ?? 0) - (a.score ?? 0);
    }
    return (b.created_utc ?? 0) - (a.created_utc ?? 0);
  });

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <h1>SignalAtlas</h1>
          <p>Owner Intelligence Suite</p>
        </div>

        <div className="sidebar-section">
          <div className="section-title">
            <h3>Your Products</h3>
            <span>{products.length}</span>
          </div>
          <div className="product-list">
            {products.map((item) => (
              <button
                key={item.product_id}
                className={`product-item ${
                  selectedProduct?.product_id === item.product_id
                    ? "active"
                    : ""
                }`}
                onClick={() => setSelectedProduct(item)}
                type="button"
              >
                <div>
                  <strong>{item.name}</strong>
                  <small>Added {new Date(item.created_at).toLocaleDateString()}</small>
                </div>
              </button>
            ))}
            {products.length === 0 && (
              <p className="status">Add a product to begin.</p>
            )}
          </div>
        </div>

        <div className="sidebar-section">
          <div className="section-title">
            <h3>Add Product</h3>
          </div>
          <input
            type="text"
            placeholder="e.g., iPhone"
            value={newProduct}
            onChange={(event) => setNewProduct(event.target.value)}
          />
          <button type="button" className="primary" onClick={createProduct}>
            Add to Portfolio
          </button>
          <div className="chip-row">
            {quickStarts.map((item) => (
              <button
                key={item}
                type="button"
                className="chip"
                onClick={() => setNewProduct(item)}
              >
                {item}
              </button>
            ))}
          </div>
          {error && <p className="status error">{error}</p>}
        </div>
      </aside>

      <main className="main">
        <header className="top-bar">
          <div>
            <p className="eyebrow">Portfolio Overview</p>
            <h2>
              {selectedProduct
                ? `Insights for ${selectedProduct.name}`
                : "Select a product"}
            </h2>
            <p className="lede">
              Run the pipeline to capture archetypes, then model topics when you
              want deeper insight.
            </p>
          </div>
          <div className="metrics">
            <div className="metric">
              <span>Subreddits</span>
              <strong>{stats ? stats.subreddits : "--"}</strong>
            </div>
            <div className="metric">
              <span>Posts</span>
              <strong>{stats ? stats.posts : "--"}</strong>
            </div>
            <div className="metric">
              <span>Comments</span>
              <strong>{stats ? stats.comments : "--"}</strong>
            </div>
            <button
              type="button"
              className="outline refresh"
              onClick={refreshPipeline}
              disabled={refreshLoading}
            >
              {refreshLoading ? "Refreshing..." : "Refresh New Posts"}
            </button>
          </div>
        </header>

        <section className="pipeline">
          <form onSubmit={runPipeline}>
            <input
              type="text"
              placeholder="Select a product from the left"
              value={selectedProduct ? selectedProduct.name : ""}
              readOnly
            />
            <button type="submit" className="primary" disabled={loading}>
              {loading ? "Running..." : "Run Pipeline"}
            </button>
          </form>
        </section>

        <section className="board">
          <div className="board-header">
            <div>
              <h3>User Archetypes</h3>
              <p>Click a segment to review the original comments.</p>
            </div>
            <div className="status-pill">
              {loading
                ? "Pipeline running"
                : topicsLoading
                ? "Topic modeling"
                : "Ready"}
            </div>
          </div>
          <div className="archetype-grid">
            {archetypes.length === 0 && !loading && (
              <div className="empty-state">
                <h4>No archetypes yet</h4>
                <p>Run the pipeline to populate archetypes.</p>
              </div>
            )}
            {archetypes.map((archetype, index) => (
              <button
                key={`${archetype.name}-${index}`}
                className={`archetype-card ${
                  index === activeIndex ? "active" : ""
                }`}
                onClick={() => setActiveIndex(index)}
                type="button"
              >
                <span className="emoji">{archetype.emoji || "\u2605"}</span>
                <div>
                  <h4>{archetype.name || "Unnamed archetype"}</h4>
                  <p>{archetype.description || "No description yet."}</p>
                </div>
              </button>
            ))}
          </div>
        </section>

        {activeArchetype && (
          <section className="detail">
            <div className="detail-header">
              <div>
                <p className="eyebrow">Archetype Detail</p>
                <h3>
                  {activeArchetype.emoji || "\u2605"} {activeArchetype.name}
                </h3>
                <p className="lede">
                  {activeArchetype.description || "No description provided."}
                </p>
              </div>
            <div className="detail-actions">
              <button
                type="button"
                className="outline"
                onClick={runTopics}
                disabled={topicsLoading}
              >
                {topicsLoading ? "Modeling Topics..." : "Run Topic Modeling"}
              </button>
                <span>
                  {data?.topics_ready ? "Topics ready" : "Topics not generated"}
                </span>
              </div>
            </div>
            {activeArchetype.topics?.length > 0 && (
              <div className="topic-row">
                {activeArchetype.topics.map((topic) => (
                  <div key={topic.topic_id} className="topic-chip">
                    <strong>Topic {topic.topic_id}</strong>
                    <p>{topic.keywords.join(" · ")}</p>
                  </div>
                ))}
              </div>
            )}
            {satisfaction && (
              <div className="satisfaction-panel">
                <div className="board-header">
                  <div>
                    <h3>Customer Satisfaction (ACSI)</h3>
                    <p>{satisfaction.model?.citation}</p>
                  </div>
                  <div className="satisfaction-actions">
                    <div className="score-ring">
                      <svg viewBox="0 0 120 120">
                        <circle
                          cx="60"
                          cy="60"
                          r="48"
                          stroke="#2a2f3e"
                          strokeWidth="10"
                          fill="none"
                        />
                        <circle
                          cx="60"
                          cy="60"
                          r="48"
                          stroke="#ffb347"
                          strokeWidth="10"
                          fill="none"
                          strokeDasharray={2 * Math.PI * 48}
                          strokeDashoffset={
                            2 * Math.PI * 48 * (1 - activeMetricAverage / 100)
                          }
                          strokeLinecap="round"
                        />
                      </svg>
                      <div>
                        <strong>{Math.round(activeMetricAverage)}</strong>
                      </div>
                    </div>
                    <a
                      href={satisfaction.model?.link}
                      target="_blank"
                      rel="noreferrer"
                      className="comment-link"
                    >
                      View paper
                    </a>
                  </div>
                </div>
                <div className="metric-grid">
                  {(satisfaction.archetypes || [])
                    .filter((item) => item.name === activeArchetype.name)
                    .flatMap((item) => item.metrics || [])
                    .map((metric) => {
                      const metricId = `${activeArchetype.name}-${metric.metric}`;
                      const isOpen = expandedMetric === metricId;
                      const evidence = (metric.evidence_comment_ids || [])
                        .map((id) =>
                          activeArchetype.comments?.find(
                            (comment) => String(comment.comment_id) === String(id)
                          )
                        )
                        .filter(Boolean);
                      return (
                        <button
                          key={metricId}
                          type="button"
                          className={`metric-card ${isOpen ? "active" : ""}`}
                          onClick={() =>
                            setExpandedMetric(isOpen ? null : metricId)
                          }
                        >
                          <div className="metric-header">
                            <strong>{metric.metric}</strong>
                            <span>{metric.score ?? 0}/100</span>
                          </div>
                          {isOpen && (
                            <div className="metric-detail">
                              <p>{metric.reasoning || "No reasoning provided."}</p>
                              <p>Confidence: {metric.confidence ?? 0}</p>
                              {evidence.length > 0 && (
                                <div className="metric-evidence">
                                  {evidence.map((comment) => (
                                    <blockquote key={comment.comment_id}>
                                      {comment.body}
                                    </blockquote>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </button>
                      );
                    })}
                </div>
              </div>
            )}
            <div className="comment-controls">
              <span>Sort by</span>
              <button
                type="button"
                className={commentSort === "recent" ? "active" : ""}
                onClick={() => setCommentSort("recent")}
              >
                Most recent
              </button>
              <button
                type="button"
                className={commentSort === "score" ? "active" : ""}
                onClick={() => setCommentSort("score")}
              >
                Top score
              </button>
            </div>
            <div className="comment-list">
              {sortedComments.map((comment) => (
                <article key={comment.comment_id} className="comment-card">
                  <p>{comment.body}</p>
                  <div className="comment-meta">
                    <span>{comment.author || "anonymous"}</span>
                    <span>{comment.subreddit || "r/unknown"}</span>
                    <span>{comment.post_title || "Post"}</span>
                    <span>{formatTimestamp(comment.created_utc)}</span>
                    <span>Score: {comment.score ?? 0}</span>
                    {comment.permalink && (
                      <a
                        className="comment-link"
                        href={comment.permalink}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open on Reddit
                      </a>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {satisfactionHistory.length > 0 && (
          <section className="history">
            <div className="board-header">
              <div>
                <h3>Satisfaction Timeline</h3>
                <p>Overall score shifts after each refresh.</p>
              </div>
            </div>
            <div className="timeline-chart">
              <svg viewBox="0 0 600 220" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="scoreGlow" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#ff7f50" />
                    <stop offset="100%" stopColor="#ffb347" />
                  </linearGradient>
                </defs>
                {(() => {
                  const width = 600;
                  const height = 180;
                  const padding = 20;
                  const points = satisfactionHistory.map((entry, index) => {
                    const x =
                      satisfactionHistory.length === 1
                        ? width / 2
                        : padding +
                          (index / (satisfactionHistory.length - 1)) *
                            (width - padding * 2);
                    const score = Math.min(Math.max(entry.overall_score ?? 0, 0), 100);
                    const y =
                      height - padding - (score / 100) * (height - padding * 2);
                    return { x, y, score, entry };
                  });
                  if (points.length === 0) return null;
                  const path = points
                    .map((point, index) =>
                      `${index === 0 ? "M" : "L"}${point.x},${point.y}`
                    )
                    .join(" ");
                  return (
                    <g>
                      <path
                        d={path}
                        fill="none"
                        stroke="url(#scoreGlow)"
                        strokeWidth="4"
                      />
                      {points.map((point, index) => (
                        <g key={`${point.entry.created_at}-${index}`}>
                          <circle
                            cx={point.x}
                            cy={point.y}
                            r="6"
                            fill="#0c0f16"
                            stroke="#ffb347"
                            strokeWidth="3"
                          />
                          <text
                            x={point.x}
                            y={point.y - 14}
                            textAnchor="middle"
                            fill="#ffb347"
                            fontSize="12"
                          >
                            {Math.round(point.score)}
                          </text>
                        </g>
                      ))}
                    </g>
                  );
                })()}
              </svg>
              <div className="timeline-labels">
                {satisfactionHistory.map((entry, index) => (
                  <span key={`${entry.created_at}-${index}`}>
                    {new Date(entry.created_at).toLocaleDateString()}
                  </span>
                ))}
              </div>
            </div>
          </section>
        )}

      </main>
    </div>
  );
}

export default App;
