import { useEffect, useState } from "react";
import WeightChart from "./WeightChart";

export default function App() {
  const [weights, setWeights] = useState([]);

  useEffect(() => {
    // /api is proxied to the backend in dev (vite.config.js) and via nginx in Docker.
    fetch("/api/weights")
      .then((res) => res.json())
      .then((data) => {
        // API returns newest-first; reverse so the chart reads left-to-right chronologically.
        setWeights([...data].reverse());
      });
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Palantiring my life</h1>
      <h2>Weight</h2>
      <WeightChart data={weights} />
    </div>
  );
}
