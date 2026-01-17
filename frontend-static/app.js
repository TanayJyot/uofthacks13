const { useState } = React;

function App() {
  const [product, setProduct] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);
  const [activeIndex, setActiveIndex] = useState(0);

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
        throw new Error(payload.error || "Pipeline failed");
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
      <section className="hero">
        <div>
          <h1>Identity Archetype Explorer</h1>
          <p>
            Type in a product, pull Reddit signals, and discover user archetypes
            shaped by what people actually say.
          </p>
        </div>
        <form className="form" onSubmit={runPipeline}>
          <input
            type="text"
            placeholder="Try: iPhone, Notion, Tesla"
            value={product}
            onChange={(event) => setProduct(event.target.value)}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Running..." : "Run Pipeline"}
          </button>
        </form>
        {error && <div className="status">{error}</div>}
        {data && (
          <div className="status">
            Scanned {data.subreddits.length} subreddits · {data.posts.length} posts
          </div>
        )}
      </section>

      {archetypes.length > 0 && (
        <section className="section">
          <h2>User Archetypes</h2>
          <div className="archetype-grid">
            {archetypes.map((archetype, index) => (
              <div
                key={`${archetype.name}-${index}`}
                className={
                  "archetype-card" + (index === activeIndex ? " active" : "")
                }
                onClick={() => setActiveIndex(index)}
                role="button"
                tabIndex={0}
                onKeyPress={(event) => {
                  if (event.key === "Enter") {
                    setActiveIndex(index);
                  }
                }}
              >
                <span>{archetype.emoji || "👤"}</span>
                <h3>{archetype.name || "Unnamed archetype"}</h3>
                <p className="status">{archetype.comments?.length || 0} comments</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {activeArchetype && (
        <section className="section">
          <div className="details">
            <h3>
              {activeArchetype.emoji || "👤"} {activeArchetype.name}
            </h3>
            <p>{activeArchetype.description || "No description provided."}</p>
            <ul className="comment-list">
              {(activeArchetype.comments || []).map((comment) => (
                <li key={comment.comment_id}>{comment.body}</li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
