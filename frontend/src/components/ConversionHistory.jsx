
import { useEffect, useState } from "react";

import {
  getConversionHistory,
  deleteConversion
} from "../services/historyService.js";

function ConversionHistory({ refreshKey, onLoad }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);

      try {
        const data = await getConversionHistory();
        setHistory(data.history);
        setError("");
      } catch {
        setError("Failed to load history");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [refreshKey]);

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this conversion?")) {
      return;
    }

    try {
      await deleteConversion(id);

      setHistory((prev) =>
        prev.filter((item) => item._id !== id)
      );
    } catch {
      setError("Failed to delete conversion");
    }
  };

  if (loading) return <p>Loading history...</p>;

  return (
    <section className="history-section">
      <h2>Conversion History</h2>

      {error && <p className="error">{error}</p>}

      {history.length === 0 ? (
        <p>No conversions saved yet.</p>
      ) : (
        history.map((item) => (
          <div className="history-card" key={item._id}>
            <div>
              <strong>
                {item.sourceLanguage.toUpperCase()}
                {" → "}
                {item.targetLanguage.toUpperCase()}
              </strong>

              <p>Method: {item.method}</p>

              <small>
                {new Date(item.createdAt).toLocaleString()}
              </small>
            </div>

            <div className="actions">
              <button onClick={() => onLoad(item)}>
                Load
              </button>

              <button onClick={() => handleDelete(item._id)}>
                Delete
              </button>
            </div>
          </div>
        ))
      )}
    </section>
  );
}

export default ConversionHistory;
