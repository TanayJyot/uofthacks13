import { useMemo, useState } from "react";
import "./App.css";

const quickStarts = [
  "iPhone",
  "Notion",
  "Tesla",
  "AirPods Pro",
  "Duolingo",
  "Figma",
];

function App() {
  const [product, setProduct] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);
  const [activeIndex, setActiveIndex] = useState(0);

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

  const runPipeline = async (event) => {
    event.preventDefault();
    if (!product.trim()) {
      setError("Enter a product name.");
      return;
    }
    setLoading(true);
    setError("");
    setData(null);

    try {
      const response = await fetch("http://localhost:5000/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product: product.trim() }),
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
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const archetypes = data?.archetypes || [];
  const activeArchetype = archetypes[activeIndex];

  return (
    <div className="app">
      <header className="top-bar">
        <div className="logo">
          <span>ARC</span>
        </div>
        <nav>
          <button className="ghost">Signal Map</button>
          <button className="ghost">Launch Shift</button>
          <button className="ghost">Reports</button>
        </nav>
        <div className="status-pill">Community Intelligence</div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Brand Identity Radar</p>
          <h1>See the people behind the product signals.</h1>
          <p className="lede">
            We turn Reddit conversations into distinct user archetypes. Every
            cluster links to the words people actually wrote — no paraphrasing,
            no guesswork.
          </p>
          <form className="form" onSubmit={runPipeline}>
            <input
              type="text"
              placeholder="Enter a product name"
              value={product}
              onChange={(event) => setProduct(event.target.value)}
            />
            <button type="submit" disabled={loading}>
              {loading ? "Mapping..." : "Run Pipeline"}
            </button>
          </form>
          <div className="chip-row">
            {quickStarts.map((item) => (
              <button
                key={item}
                type="button"
                className="chip"
                onClick={() => setProduct(item)}
              >
                {item}
              </button>
            ))}
          </div>
          {error && <div className="status error">{error}</div>}
        </div>

        <div className="hero-panel">
          <div className="metric-card">
            <p>Signal pass</p>
            <h2>{stats ? stats.subreddits : "—"}</h2>
            <span>Subreddits scanned</span>
          </div>
          <div className="metric-card">
            <p>Conversation set</p>
            <h2>{stats ? stats.posts : "—"}</h2>
            <span>Hot posts pulled</span>
          </div>
          <div className="metric-card">
            <p>Identity samples</p>
            <h2>{stats ? stats.comments : "—"}</h2>
            <span>Comments clustered</span>
          </div>
          <div className="hero-glow" />
        </div>
      </section>

      <section className="board">
        <div className="board-header">
          <div>
            <h2>User Archetypes</h2>
            <p>
              Click any persona to read the raw comments that formed the
              identity cluster.
            </p>
          </div>
          <div className="pipeline-status">
            <span>{loading ? "Running pipeline..." : "Ready"}</span>
            <div className={`dot ${loading ? "live" : ""}`} />
          </div>
        </div>

        <div className="archetype-grid">
          {archetypes.length === 0 && !loading && (
            <div className="empty-state">
              <h3>Awaiting a product signal.</h3>
              <p>Run the pipeline to generate archetypes and quotes.</p>
            </div>
          )}
          {archetypes.map((archetype, index) => (
            <button
              key={`${archetype.name}-${index}`}
              className={`archetype-card ${index === activeIndex ? "active" : ""}`}
              onClick={() => setActiveIndex(index)}
              type="button"
            >
              <div className="card-top">
                <span className="emoji">{archetype.emoji || "👤"}</span>
                <span className="count">
                  {archetype.comments?.length || 0} comments
                </span>
              </div>
              <h3>{archetype.name || "Unnamed archetype"}</h3>
              <p>
                {archetype.description
                  ? archetype.description.slice(0, 90)
                  : "No description provided yet."}
              </p>
            </button>
          ))}
        </div>
      </section>

      {activeArchetype && (
        <section className="detail-panel">
          <div className="detail-header">
            <div>
              <p className="eyebrow">Selected Archetype</p>
              <h2>
                {activeArchetype.emoji || "👤"} {activeArchetype.name}
              </h2>
              <p className="lede">
                {activeArchetype.description || "No description provided."}
              </p>
            </div>
            <div className="summary-card">
              <span>Evidence</span>
              <strong>{activeArchetype.comments?.length || 0}</strong>
              <p>original comments</p>
            </div>
          </div>
          <div className="comment-list">
            {(activeArchetype.comments || []).map((comment) => (
              <article key={comment.comment_id} className="comment-card">
                <p>{comment.body}</p>
                <div className="comment-meta">
                  <span>{comment.author || "anonymous"}</span>
                  <span>Score: {comment.score ?? 0}</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default App;
