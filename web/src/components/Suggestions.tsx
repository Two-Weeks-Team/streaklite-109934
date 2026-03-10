import { useEffect, useState } from 'react';
import { getRecommendations, Recommendation } from '@/lib/api';

export default function Suggestions() {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await getRecommendations();
        setRecs(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <p className="my-4">Loading habit suggestions...</p>;
  if (recs.length === 0) return null;

  return (
    <section className="my-6 p-4 border rounded bg-white shadow-sm">
      <h2 className="text-xl font-semibold mb-2">AI‑Powered Recommendations</h2>
      <ul className="list-disc list-inside space-y-1">
        {recs.map((r, idx) => (
          <li key={idx}>
            <strong>{r.name}</strong> – {r.reason}
          </li>
        ))}
      </ul>
    </section>
  );
}