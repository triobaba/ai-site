import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import ReactMarkdown from 'react-markdown';

export default function App() {
  const [site, setSite] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [citations, setCitations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!site || !question) return;
    setLoading(true);
    setAnswer('');
    setCitations([]);
    setError('');
    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ site, question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
      setAnswer(data.answer);
      setCitations(data.citations || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-5">
      <h1 className="text-center mb-4">AI Site Search</h1>
      <form className="card p-4 shadow-sm" onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="site" className="form-label">Site URL</label>
          <input id="site" className="form-control" value={site} onChange={(e) => setSite(e.target.value)} placeholder="example.com" required />
        </div>
        <div className="mb-3">
          <label htmlFor="question" className="form-label">Question</label>
          <textarea id="question" className="form-control" rows="3" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="What is on the pricing page?" required />
        </div>
        <button className="btn btn-primary" type="submit" disabled={loading}>{loading ? 'Searching…' : 'Search'}</button>
      </form>

      {(answer || error) && (
        <div className="card mt-4 p-4 shadow-sm">
          {error ? (
            <div className="text-danger">Error: {error}</div>
          ) : (
            <>
              <h5>Answer</h5>
              <ReactMarkdown
                components={{
                  a: ({ node, ...props }) => (
                    <a {...props} target="_blank" rel="noopener noreferrer" />
                  ),
                }}
              >
                {answer}
              </ReactMarkdown>
              {citations.length > 0 && (
                <div className="mt-4">
                  <h6>Sources</h6>
                  <ol className="small">
                    {citations.map((c) => (
                      <li key={c.index}>
                        <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-decoration-none">
                          {c.url}
                        </a>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
} 